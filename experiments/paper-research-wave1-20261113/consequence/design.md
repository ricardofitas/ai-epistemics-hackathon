# Small PAWS-to-NLI decision-consequence pilot

**Prepared only. No model inference has been executed.** This design must be separately frozen and may run only if the ongoing recommendation replication finds the same PAWS-to-directional-NLI sufficiency error in at least two of three **completed** fresh responses for at least one configuration. That is a descriptive activation rule, not statistical significance or a guarantee of publishability. If fewer than three responses complete, or the mechanism is not repeated, this gate is not met.

The aim is to move one step beyond an advice-text error: test whether a PAWS-based proxy would select a different fixed candidate from a role-sensitive NLI criterion, then measure the selected candidates on an independent target-confirmation subset. A null, tie or incomplete result is a valid outcome.

## Authentic source data

- **PAWS-Wiki Labeled (Final), test:** 8,000 human-labeled pairs in the public release. The official repository at `02b29f3af1143620d1b7f352247e65c0bdd2ec18` documents the test split and binary meaning-equivalence labels. The canonical GCS archive returned HTTP 403 here. The actual data used are the byte-pinned Hugging Face mirror under `google-research-datasets/paws`, revision `161ece9501cf0a11f3e48bd356eaa82de46d6a09`, file `labeled_final/test-00000-of-00001.parquet`. SHA256 is `ae342ff12bb84b84b95f468abf5db6cb7c7bd578271299fe9c99be75b8132f4d`. Byte identity to the inaccessible original tar archive was **not** verified; do not hide that provenance limit.
- **HANS:** the official `heuristics_evaluation_set.txt` at commit `7299f6f657089ce06a0f98e7e81f8d0f5b7741ce`, 30,000 rows. SHA256 `c55b62feef9913070e88f38938dc2492018c945ac81f70139346472494124e79`; Git blob `e042af242b19708d9c0256c713e873415c0b58a1` matches the official tree. The exact eligible strata each contain 1,000 rows: `ln_subject/object_swap` / non-entailment and `le_passive` / entailment.

Actual downloaded source data total 16,697,190 bytes, below the 30 MB budget. Keep the small selected data, source metadata, hashes and sampler in the project; the full source cache is reproducible and need not be committed. A public test split is not proof of exclusion from these models' pretraining. HANS is a narrow templatic diagnostic, not general English understanding. Original annotations are retained without performance-dependent filtering or relabeling.

## Selection fixed before performance

`selection_intent.json` declares seed `2026111311` and the two requested model configurations before data inspection. `download_and_select.py` reproduces source checks and sampling.

1. Randomly sample ten PAWS label-0 and ten label-1 test pairs, without replacement, using original source order and a fixed Python RNG.
2. Randomly sample ten HANS non-entailing subject/object swaps and ten entailing passives. These are independently sampled strata, **not matched sentence pairs**.
3. Shuffle each selected HANS stratum; assign its first five to target selection and last five to target confirmation. This yields **10 target-selection items and 10 independent target-confirmation items**, each balanced five/five.

No model predictions, errors, disagreement or likely difficulty were used to select items. The 40 source items and source row IDs/indices/golds appear in `selected_data.json` and `selection_manifest.json`.

## Common classification interface and explicit proxy adapter

Requested candidates are `gemma-4-31b-it` and `qwen3.8-27b`, chosen for prior operational completion before their performance on these items. Requested/returned aliases must be retained; exact immutable weights are not established.

Both candidates receive the same ordinary three-way NLI instruction: label an ordered premise/hypothesis pair entailment, contradiction or neutral, using only the premise. The answer is JSON containing supplied opaque IDs and labels, with no explanation. Model-facing inputs contain no benchmark names, suite membership, source metadata or gold labels.

For each PAWS pair, classify **both directions**. The explicit proxy adapter predicts paraphrase only when both directions are entailment; otherwise it predicts non-paraphrase. Score against original PAWS binary labels. For HANS, classify the original direction and collapse contradiction/neutral to non-entailment, following its documented scoring.

This adapter is a deliberately specified repair of an underspecified recommendation. The original bad advice did not supply it. Approximate human paraphrase annotations need not exactly coincide with strict mutual entailment, so its validity is a stated limitation. Even a useful paraphrase proxy does not make its aggregate accuracy sufficient for the requested directional role capability.

There are 40 PAWS directions and 20 HANS ordered inputs per model: 60 labels each, 120 labels total. The pool is shuffled with seed `2026111312` and assigned opaque IDs. Preserve that relative shuffled order within each analysis role, then batch five inputs per request separately: eight PAWS proxy batches, two HANS target-selection batches and two HANS target-confirmation batches. No confirmation input shares a request with selection or proxy inputs. Both candidates receive identical batch membership/order. Twenty-four request rows are shuffled with seed `2026111314`. `manifest.jsonl` contains the complete proposed requests; row-level `batch_role` and `task_key.json` are evaluator-only and are never transmitted.

The proposed payload uses temperature 0, an 8,192 generated-token cap, streaming, no tools, no history, no agentic memory and `store=false`. Concurrency is two; timeout is 120 seconds per socket operation, not a total-duration promise. All 24 client requests must be attempted once; no hidden retry, repair request, replacement item or extra model is allowed. The common cap gives at most 196,608 generated tokens. Costs and transport failures must be recorded rather than inferred from a presumed account balance.

## Selection, consequences and ties

The **proxy winner** is the unique higher PAWS accuracy on all 20 sampled pairs. The **target winner** is the unique higher HANS accuracy on the 10 selection items. If either score ties, there is no unique choice and the primary reversal/consequence is indeterminate; do not manufacture a winner with an arbitrary tie-break.

A strict score-order reversal requires nonzero opposite signs for the two candidates' PAWS difference and HANS-selection difference. If both winners are unique, the primary observed consequence is:

`target-selected candidate accuracy − proxy-selected candidate accuracy`

on the independent **10-item HANS confirmation subset**. This difference may be positive, zero or negative; report all possibilities. The full 20-item HANS score ordering may be shown as secondary description, but must not be recycled as supposedly independent confirmation after selecting by those same items.

Report per-stratum accuracy, original class denominators, prediction coverage, invalid output and all API failures. Primary analysis requires valid complete predictions for every planned ordered input for both models. Otherwise the primary pilot is incomplete. Any available-item score must be clearly secondary with its reduced denominator, not silently called complete or used to infer semantic failure from missing transport output.

A fixed parser may accept an entire JSON object with a predictions array, optionally removing one outer JSON code fence. It must check exact expected IDs, no duplicates/extras, and the three allowed labels (case-folding allowed). Do not call a model to repair an answer or infer a missing label. Keep exact raw final text and provider status.

The prospective offline analyzer applies explicit capture-quality requirements beyond the runner's `completed_nonempty` flag: HTTP 200, `text/event-stream` content type, native SSE parsing without a format deviation, zero malformed SSE JSON frames, and one nonpartial `response.completed` terminal event with provider status `completed`. Transport/provider errors, incomplete details, a missing terminal or delta fallback prevent a valid completed batch. It checks exact frozen request payloads and their canonical hashes, individual artifacts against the aggregate, terminal objects and assistant text against durable journals, journal/text hashes and capture times after the separate freeze. An integrity contradiction blocks analysis. Missing or invalid evidence gives no primary score and is never imputed as a semantic error. Requested and returned aliases remain descriptive evidence; alias equality is not an additional completeness exclusion and immutable weight identity remains unverified.

## Uncertainty and interpretation

Use 10,000 paired bootstrap draws with seed `2026111313`. Resample 10 PAWS pairs with replacement within each original binary-label stratum, jointly across directions and models. Independently resample five HANS items with replacement within each prespecified analysis-role × original-label stratum, jointly across models; keep confirmation separate from selection. Report two-sided 95% equal-tailed percentile intervals using the 0.025 and 0.975 quantiles with linear interpolation. For realized confirmation regret, hold the observed proxy and target winners fixed rather than selecting them anew in bootstrap draws. These are conditional item-resampling intervals, not uncertainty over model reruns, alternate batch contexts, article/topic clusters or candidate selection. This tiny curated sample can produce wide or degenerate bootstrap intervals; a tie, nonsignificance or degenerate zero interval does not prove model equivalence. No formal significance claim is planned.

An input-only prereview flagged an apparent annotation issue in `P-19`: the original PAWS label is paraphrase, while one sentence says `b. 1951` and the other says `died 1951`. The original gold and selected item remain unchanged. This a priori caveat is not grounds for a performance-dependent exclusion or relabeling. Other awkward or approximate source annotations may also remain.

This is an intentionally small progression toward actual consequences, not a definitive benchmark comparison. A differing choice would illustrate a bounded consequence for two candidate configurations under this adapter and sample. It would not demonstrate actual human adoption/harm, representative prevalence or an intrinsic PAWS defect. A larger fresh target holdout and human annotation review would be needed for a strong paper claim.

## Reproduction and publication

Run `download_and_select.py` with `pyarrow` installed; `--pyarrow-path` can point to an existing dependency directory. Source hashes are checked before sampling. `selected_data.json` and `manifest.jsonl` are deterministic; generated timestamps in the selection receipt can change on rerun. No model call is made by the sampler.

Before any inference, freeze `protocol.json`, `selection_intent.json`, `selected_data.json`, `selection_manifest.json`, `task_key.json`, `manifest.jsonl`, source metadata and sampler code in a separate commit. Confirm the recurrence gate from the independent recommendation ratings first. The current status is prepared-only, zero model calls.

`analyze_consequence.py` is implemented and verified only with fabricated temporary fixtures; `analyzer_verification.json` records 41 synthetic checks and independent read-only prereview. Its exact hash, the native SSE runner and all analysis inputs must be pinned before any future execution. Actual analysis additionally requires externally supplied `gate_activation.json` evidence identifying exactly three completed fresh original-question replicates of one qualifying configuration, at least two adjudicated as the exact PAWS-to-directional-NLI mechanism. A different label-conversion error cannot satisfy this gate. The gate must precede the separate consequence freeze. CLI arguments supply that commit/time, frozen protocol SHA256 and frozen gate SHA256; the commit is explicitly caller-attested rather than independently fetched from Git. The helper makes no network calls and creates a new `analysis/results.json` and `analysis/predictions.jsonl` only after its checks pass. The original prereview remains unchanged; subsequent analyzer review is recorded in a separate addendum. The separate `NOT_RUN_STATUS.json` records the gate outcome without rewriting these prospective definitions.

Primary definitions:

- https://github.com/google-research-datasets/paws/blob/02b29f3af1143620d1b7f352247e65c0bdd2ec18/README.md
- https://aclanthology.org/N19-1131/
- https://github.com/tommccoy1/hans/blob/7299f6f657089ce06a0f98e7e81f8d0f5b7741ce/README.md
- https://aclanthology.org/P19-1334/
