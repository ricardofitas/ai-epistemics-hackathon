# One-shot prospective P1 gap replication

Runs the separately frozen source-disjoint 30-family replication using the existing private execution repository credential. Two format-only admission requests precede 80 fixed study requests. Arithmetic correctness is never an admission criterion. No retry, model substitution, source edit or automatic resumption is allowed.

After full source review and the external source/protocol/code freeze:

```sh
python ci_gap_p1_launch2_20261113/prepare_launch.py --source-freeze-commit <40-hex-commit>
cp ci_gap_p1_launch2_20261113/LAUNCH.template.json experiments/gap-replication-20261113/runtime/LAUNCH.json
python ci_gap_p1_launch2_20261113/execute.py preflight
```

Publish exact frozen runtime files, unchanged native-SSE runner, execute.py, execution_pins.json and workflow to the new branch `ricardo/epistemics-gap-p1-launch2-20261113` of the execution repository. The single LAUNCH.json push triggers execution. Main inference budget is 80 requests / 655,360 maximum requested output tokens; total including admission is 82 / 671,744. Capture concurrency is two and the socket-operation timeout is 120 seconds. A 90-minute capture wall limit and 120-minute job limit leave time for evidence retention. Incomplete results remain incomplete.

The wrapper checks source/protocol/code hashes before credential use, exact question payloads, no gold or family metadata in prompts, 30 distinct families in ten common blocks, each task once per model, native-SSE runner pin, one-shot workflow history, fixed model catalogue aliases, and the exact credential does not appear in retained artifacts.

Offline guard tests: `python -m unittest discover -s ci_gap_p1_launch2_20261113 -p test_execute.py -v`.

The first launch stopped in the history guard before provider access. This explicit infrastructure-only amendment verifies the exact current run through its direct metadata endpoint, while the paginated branch listing separately rejects prior matching runs. A lagging current-run listing is accepted only after direct ID, head SHA, branch, event, workflow path and attempt checks pass. No provider request is retried. See the preserved first-launch evidence and amendment in the study root.
