# Private GAMMAF repair executor

Prepared for `rfitas-lab/rfdl-lab-os`, branch
`epistemics/gammaf-v2-repair-20261115`. No remote mutations or inference were
performed while preparing these files.

Copy this directory into `experiments/gammaf-v2-repair-20261115/`; copy
`gammaf-v2-repair.yml` to `.github/workflows/gammaf-v2-repair.yml`.

Before creating the launch marker, the research owner must supply:

- `plan.json` with `max_api_calls` (at most 5000) and `max_credits` (at most 100),
  the fixed cohort, arms, model parameters, stopping rules and UTC cutoff.
- `executor-config.json` with `study` equal to
  `gammaf-v2-full-options-20261115`, `plan_path` equal to `plan.json`, its
  exact `plan_sha256`, `deadline_utc`, `preflight_command` and
  `inference_command` arrays. Commands run from this directory; inference is
  invoked without a shell, with the credential in the child environment only.
- The Python package, exact question and option records, fixed selection,
  meaningful offline tests, and `requirements-executor.txt`.
- `FREEZE.json` containing a `files` mapping from every package/plan/config
  filename to its SHA-256. Exclude `FREEZE.json`, `LAUNCH.json`, runtime output
  and the credential-delivery directory itself. Do not exclude code or inputs.
- `LAUNCH.json` containing `study` and `plan_sha256`, created only after offline
  review. Pushing any other path does not launch this workflow.

The workflow publishes its fresh X25519 public key in a public-key artifact
whose name is `gammaf-key-RUN_ID-PUBLIC_SPKI_BASE64URL`. It waits at most twenty
minutes for authenticated encrypted delivery at
`experiments/gammaf-v2-repair-20261115/credential-delivery/RUN_ID.sealed.json`
on the same branch. The envelope must use protocol `rfdl-gammaf-sealed-v1`,
HKDF-SHA256 info `protocol + NUL + exact AAD bytes`, AES-256-GCM, and exact
run/commit/plan/freeze/deadline context from `credential-public.json`.

The executor hard-stops before the six-hour job boundary, leaving five minutes
for result upload. It also respects the earlier explicit UTC cutoff. It first
requests SIGINT for checkpointing, then SIGTERM after 25 seconds and SIGKILL
after 35 seconds. Only the first workflow attempt can execute. The paid runner
must additionally enforce plan call/credit/clock caps before every request.

Never put a plaintext credential, token, account key or private exchange key
in the repository or artifacts. Only the run-bound encrypted envelope is
committed. The existing RFDL successful Wino/SIQA executor used this same
credential-delivery pattern; those old workflows and studies are untouched.
