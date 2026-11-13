# Frozen wave analysis

`collect_wave.py` audits all 60 planned attempts, including errors, against the
frozen manifest and individual artifacts. It checks payload/text hashes,
aggregate equality, starts after the caller-supplied Git freeze timestamp, durable
SSE journal hashes, final terminal text, and conservative completion flags.
Git commit/time are caller-verified inputs; the helper makes no network lookup.
A local capture exception remains an incomplete, unverifiable attempted row.
Provider terminal event names and their nested response statuses are retained
exactly as received, even when contradictory. Matching artifact/journal/receipt
bytes still pass the integrity audit; derived `terminal_status_consistent` and
`event_status_mismatch` fields flag the deviation, with separate operational
counts in `integrity.json`. An event named `response.completed` wrapping status
`incomplete` remains incomplete/unscorable. Completion requires both the event
and provider status to be completed, nonempty final text, and all other
conservative completion checks. No capture or frozen protocol is rewritten.

```sh
python paper_research_20261113/collect_wave.py paper_research_20261113/study \
  --freeze-commit COMMIT_SHA --freeze-time 2026-11-13T04:20:31Z
```

The derived `review_packet.jsonl` has exactly Q01–Q60, shuffled with seed
2026111313, and only `response_id`, `case_id`, `response`, `capture_complete`,
`incomplete_details`. Models, stage, repetition, and usage are in a separate key
and enriched capture file. Repeated wording/case IDs remain visible; do not claim
perfect stage blindness. Existing packets/keys cannot be changed by rerunning.

Each independent first reviewer writes **all 60 rows** to a separate JSONL:

```json
{"response_id":"Q01","unsupported_recommendation":"yes","exact_supporting_passages":["an exact nonempty substring of the response"],"mechanisms":["wrong_source_news_period"]}
```

Primary labels are `yes`, `no`, `uncertain`, `unscorable`. Incomplete captures must
be `unscorable`. Positive labels need exact response passages and explicit
mechanism coding. `mechanisms` is an exhaustive list; an empty list explicitly
identifies none. Alternatively use `mechanism_flags`, an object with exact IDs
mapped to `yes`, `no`, or `uncertain`. Omitted flag-map entries remain uncertain.
Use one mechanism format per row. Exact IDs:

| Case | Exact target mechanism |
| --- | --- |
| open_mt_news_ende_late2019 | wrong_source_news_period |
| NEW-HANS-ROLES | paraphrase_score_sufficient_for_directional_entailment |
| NEW-BEIR-COVID-RETRIEVAL-POSITIVE | nonsignificance_implies_equivalence |

`other_material` identifies a different material error and cannot replicate a
target mechanism. Additional free-text rationale fields are allowed. Mechanism
coding expresses verification of the exact proposition, not merely topical
similarity or a generally poor recommendation.

Before unblinding, independently freeze both original review files and record:

```json
{"frozen_utc":"2026-11-13T00:00:00Z","packet_sha256":"SHA256","first_rating_sha256":{"a":"SHA256_A","b":"SHA256_B"}}
```

The script verifies these bytes before loading the key; the timestamp is a
coordinator attestation, not independently proved ordering. Preserve the original
review files; do not rewrite them with consensus labels. Use a separate JSON file:

```json
{"coordinator_dispositions":{"Q01":"yes"},"coordinator_mechanisms":{"Q01":["wrong_source_news_period"]},"rationales":{"Q01":"Explain the decision and passage."}}
```

Every primary disagreement requires an explicit disposition. Every positive
final label with a mechanism disagreement or primary-label disagreement requires
an explicit mechanism disposition. A mechanism disposition can instead be an
ID→flag object; use `uncertain` when unresolved. The summarizer fails before
claims or gate activation if required adjudication is absent. Agreement is not
external expert validation, and historical results are never pooled silently.

```sh
python paper_research_20261113/summarize_wave.py paper_research_20261113/study \
  --ratings-a path/to/first_a.jsonl --ratings-b path/to/first_b.jsonl \
  --first-review-freeze path/to/first_review_freeze.json \
  --adjudication path/to/adjudication.json
```

Primary error counts and exact-mechanism recurrence are separate. The latter
requires all three planned repetitions complete and scorable in the requested
configuration/case cell, plus at least two final `yes` labels with that case's
exact target flag `yes`. Uncertain mechanisms and different material errors do
not count. The optional consequence gate applies only to NEW-HANS-ROLES and
requires at least one eligible configuration. This is a descriptive heuristic
on fixed contexts, not a significance test or a population failure rate.
Requested and returned model aliases do not establish immutable model weights.
