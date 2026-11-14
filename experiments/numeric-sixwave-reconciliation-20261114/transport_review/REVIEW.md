# Targeted offline supplemental review

Both supplemental checks passed. The original `verified6/audit_result.json` is preserved byte-for-byte, including its 14 failures under `missing_terminal_only_http429`. This supplement validates the exception handling; it does not replace the failed original report or turn unknowns into successful terminals.

The original six-wave captures contain 2,400 unique started slots and 2,430 attempts: 2,316 completed, 70 incomplete, six `missing_terminal` and eight `http_504`. The 30 retry-triggering attempts were explicit HTTP429s. All 14 non429 terminal absences occur in wave 6 and exactly match the original failed identities: six HTTP200 streams with recorded frames but no terminal, and eight HTTP504 records with zero frames. Every one remains ineligible, has no fabricated terminal file, carries a matching predispatch intent and positive full reservation, and received no retry. Section conservative cost totals reproduce the logged progress values and remain under their ceilings. Provider-side completion and actual charges for these unknowns remain unknown; reservations are accounting safeguards, not measured spending.

The numeric sensitivity analysis was independently recomputed from numeric attempt logs, eligible terminal bytes and frozen cases without importing or executing `interpret_options.py` or the production analyzers. It exactly matches the existing option-aware pooled and per-model results:

| Numeric arm | Planned | Completed | Shown option endorsed | Source-accurate decoded answer | Reserved other text | Unknown |
|---|---:|---:|---:|---:|---:|---:|
| Correct shown value | 96 | 96 | 96 | 96 | 0 | 0 |
| Wrong shown value | 96 | 82 | 45 | 30 | 7 | 14 |

For the correct shown value, 34 answers were literal A, 61 were consistent A plus value, and one was a bare number. For the wrong shown value, 36 were literal A, nine were consistent A plus value and 30 were correct bare answers; the seven remaining text answers were left unadjudicated. The original bare-number primary endpoint remains one correct in the correct arm and 30 in the wrong arm, with 178/192 eligible responses overall. The 96/96 decoded result is explicitly post hoc, not a change to that primary metric.

There are 24 source questions repeated across four models in each arm: 96 observations per arm do not represent 96 independent sources. No provider calls, broad semantic adjudication, Git operations or durable-storage operations were performed by this review.

Reproduce offline with `python run1949/transport_review/verify_supplemental.py`. Outputs are `transport_supplemental.json` and `numeric_option_independent.json` beside that script. Raw SSE bytes are absent, so stream hashes cannot be independently rehashed here.
