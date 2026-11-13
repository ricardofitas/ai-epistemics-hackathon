# Source-reviewed math consequence pilot

The original 32-family proposal failed its source-quality gate and received no model calls. This separate 30-family cohort uses all families accepted by both source reviewers.

This prospective selected-case follow-up asks whether the same two fixed solvers
would be chosen differently by an added-clause evaluation (Apple P1/P2) versus a
task-matched evaluation of separate numerical substitution and harmless wording
changes (source-reviewed GSM-Plus rows). No reversal is assumed. Both selectors
use the same mean correctness over two variants per source family.

The source-only selection has 30 families, 15 for choice and 15 untouched for
confirmation. Family groups of three are kept identical across all four variant
types and both candidates. Thus 80 requests cover 240 item classifications.
Each request shows only opaque IDs and three unrelated questions. Gold answers,
dataset names, families, split and selection policies are not model-facing.
Provider aliases do not establish immutable weights or pretraining absence.

Before the study, one fixed three-item nonstudy request per candidate checks only
capture and answer-format compatibility. Correctness is not checked. A failed
admission stops all study inference, without retry, new prompts or replacement
candidates. There are at most 82 requests and 671,744 requested output tokens in
total, with 8192 per request, concurrency two, temperature zero and a 120-second
per-operation socket timeout. All incomplete or malformed captures are retained.

## Preparation before inference

Only after all source-review dispositions are accepted, run:

```bash
python prepare_manifest.py --selected-data selected_data.json \
  --source-manifest ../consequence_math_sources_20261113/source_manifest.json \
  --source-disposition source_disposition.json \
  --selection-plan ../consequence_math_sources_20261113/selection_plan.json \
  --runner ../../../scripts/run_adaption_stream_pilot.py
```

Use the actual runner path from the repository root if this relative example is
not applicable. The preparer checks its exact SHA256 and writes the task key,
80-request manifest, two-request admission manifest and machine protocol once.
It refuses draft source samples and existing prepared outputs. The protocol pins
source data and implementation files; it must be published and verified before
using the existing authorized CI credential. No credential belongs in this tree.

## Capture and analysis

The original unmodified native-SSE runner writes exclusive artifacts and journals
and never retries. Run it first on `admission/`, then invoke `gate_admission.py`
with the published commit/time/protocol hash. Only a passing gate permits running
the 80-request study manifest. CI orchestration is isolated in a separate branch.

After capture, `capture_math.py` replays raw SSE lines, checks request/response
hashes and requires HTTP 200, a nonempty completed provider response, a completed
terminal event, and no stream/transport/fallback deviation. Final output must be
the entire JSON object containing every exact requested ID once and no extras;
one optional outer code fence is allowed. Values must be numeric strings or
ABSTAIN. Integers, finite decimals/exponents, ratios, valid thousands commas and
a leading dollar sign are normalized to exact fractions. Representations are
capped at 128 characters and exponent magnitude 100 before exact parsing. There is no rounding
tolerance, expression execution, unit inference or format-repair request.
ABSTAIN is a known incorrect answer; invalid captures/formats remain [0,1].

`analyze_math.py` preserves all 240 planned scores, ties and unknown bounds.
Selection is identified only by a complete unique maximum or strictly separated
conservative bounds. Fixed selected candidates are compared on independent
confirmation target accuracy, including zero and negative effects; an identical
winner yields exact zero by coupling even when its accuracy is unknown. Joint
correctness on both target variants is secondary. Family and common batch-block
bootstrap summaries are descriptive conditional sensitivities; five blocks per
split give fragile uncertainty. These are separate transformations, not their
composition. Human semantic validation and a downstream user decision remain
unestablished. All source exclusions and null/incomplete results must be reported.

## Offline verification

```bash
python -m unittest discover -s . -p 'test_*.py' -v
python analyze_math.py --self-test
```

The fixtures cover exact numeric equality, ambiguous/invalid output, strict SSE
status/event checks, source-review gating, allocation, reversal, missing-outcome
bounds, same-winner coupling and both resampling units. They make no model calls.
