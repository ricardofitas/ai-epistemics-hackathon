# Source-only candidate preparation for the P1 gap replication

The frozen candidate pool contains all **50 released Apple P1 source families** absent from the previous 50-family P1/P2 pool. Every prior reviewed family is excluded, including those rejected or uncertain before the earlier solver study. Each new candidate includes official GSM-Plus numerical substitution and problem-understanding/paraphrase, plus released Apple P1 instances **0 and 1**. There is no GSM-Symbolic base or P2 task in this packet.

The two P1 instances are two realizations of P1. Averaging them is a **P1-only partial resource replication**, not an exact replication of the previous P1/P2 contrast. Numerical substitution and paraphrase are separate target examples, not a test of both transformations composed in one item.

`source_review_packet.jsonl` contains all 50 family records in frozen priority order. Neutral IDs are `P001`–`P050`; variant IDs are `numeric`, `paraphrase`, `p1_i0` and `p1_i1`. Exact source row indices, raw-line hashes, questions, verbatim source final answers, source solutions and source-family linkage accompany each variant. `gold_answer` is the exact numeric value in a canonical string representation (e.g. thousands commas removed); `source_final_answer` preserves the source final-answer string.

Rank is ascending SHA256 of UTF-8 `20261113117|` followed by the source-family ID, with family ID as a deterministic tie-break. The source gate admits exactly the first **30** candidates passing both complete independent first source reviews. An uncertain or rejected result is excluded. No coordinator override, question/gold edit or source-review revision can admit a candidate. If fewer than 30 pass, the study stops before solver inference. The single 30-family prospective replication cohort has no selection/confirmation split. Fixed blocks are selected rank slots 1–3, 4–6, ..., 28–30, identical across models and all variants.

The prescribed first-review schema is one JSONL record per candidate:

- `response_id`, `source_family_id`, `family_disposition` (`pass`, `reject`, `uncertain`), `family_issue`.
- `variant_checks`: all four neutral variant IDs, each with `computed_answer`, `gold_status` (`pass`, `fail`, `uncertain`), `target_structure_status` (`same`, `not_applicable`, `fail`, `uncertain`), `arithmetic_evidence`, `issue`.

A pass requires all four source-gold checks to pass and independently computed numeric answers to equal the unchanged source values. Numeric/paraphrase structure must be `same`, with independent arithmetic evidence for every variant. P1 variants must remain solvable and correctly linked to the original family. The reviewers must not read solver outputs or each other's judgments.

`selection_plan.json` defines source selection before either review. `source_manifest.json` pins the raw public releases and `excluded_previous_families.json` documents exclusion of all prior source families. Full original raw JSONL files remain pinned inputs and are not duplicated in this source packet directory.

Rebuild the pool in a **new** output directory from the two pinned raw source JSONL files:

```sh
python prepare_source_pool.py --source-dir /path/to/pinned/raw/sources --prior-candidates previous_candidate_families.json --inventory source_inventory.json --output-dir /path/to/new/pool
```

After freezing the pool and collecting both first-review files, run the strict source finalizer with a **nonexistent** output directory:

```sh
python finalize_source_selection.py --review-a /path/to/first_a.jsonl --review-b /path/to/first_b.jsonl --output-dir /path/to/new/selected_cohort
```

It preserves review bytes and source records, emits all-50 dispositions plus exactly 30 selected families if the gate passes, and exits without creating a cohort if fewer than 30 qualify. Offline tests use explicitly synthetic review fixtures and make no model calls:

```sh
python test_source_gate.py
```

No source admission, review launch or solver inference was performed by this preparation step. The full scientific protocol and execution freeze remain separate from this source-only preplan.
