# Prospective PAWS/HANS consequence prereview

Status: protocol and analyzer reviews passed with prospective corrections, conditional on the independent recurrence gate, final hash pinning and a separate pre-inference freeze. This is not a run authorization. No inference was performed. No ongoing recommendation output, API artifact or stream journal was read; credentials were not accessed.

The review verified the fixed source sampling and role split, explicit bidirectional PAWS adapter, original-direction HANS collapse, ties, signed consequences, complete-output requirement, native SSE compatibility and narrow descriptive interpretation. The gate was deliberately not assessed here.

## Corrections before freeze

- Original mixed batches co-presented HANS selection and confirmation inputs in four of twelve batch contexts. There was no gold-label leakage, but shared contexts weakened independent-confirmation wording. Preserved all selected source rows, opaque QIDs and relative shuffled order within role. Rebatched separately by analysis role: 8 PAWS proxy batches, 2 HANS selection batches and 2 HANS confirmation batches per model, each of five. Kept 24 total requests, identical model membership/order, unchanged instructions/settings, and seeded request-order shuffle. Row batch_role is evaluator-only and is not transmitted.
- Bootstrap confidence level, interval and quantile method were not fully specified. Fixed 10,000 paired draws at seed 2026111313; two-sided 95% equal-tailed percentile intervals at .025/.975 with linear interpolation. Resample PAWS pairs within original binary gold strata, retaining both directions and both models; independently resample HANS items within analysis-role x original-gold strata, retaining both models. Hold observed winners fixed in confirmation consequence draws; ties remain indeterminate.
- Input-only review flagged an apparent source annotation issue: P-19 has original PAWS paraphrase gold=1 despite b. 1951 versus died 1951. Recorded an a priori annotation caveat. Kept the original source item and gold unchanged; no selective exclusion, relabeling, or altered response grading.
- The protocol hash receipt did not include design/source metadata or an explicit runner pin. Refreshed all existing artifact hashes after corrections, added design/source metadata hashes, and pinned the reviewed native SSE runner SHA256.

## Verification

- Cached PAWS parquet and HANS TSV matched declared SHA256 values. An isolated temporary sampler reproduction used only those cached bytes; no network or inference was needed.
- Revised sampler reproduced selected_data.json, task_key.json and revised manifest.jsonl byte-for-byte. selection_manifest.json matched except its deliberately volatile generated_utc. Original selected files were not overwritten.
- 40 unique source items; PAWS 10 per gold; HANS selection and confirmation each 5 entailment + 5 non-entailment. No duplicate HANS source items or shared sentences across selection/confirmation. Independently sampled swap/passive strata are not matched sentence pairs.
- Payload input entries contain only opaque id, premise and hypothesis. No gold, suite, source ID, analysis role or evaluation metadata transmitted. Role-separated requests now avoid co-presentation of confirmation and selection items; source-public/pretraining contamination remains unknown.
- All 24 payloads already used stream=true before prereview and still do. The native runner explicitly requires stream=true in load_manifest; it validates standalone inputs, output caps, no history/tools/memory and store=false. It records terminal status, deltas/fallback flags, raw final output, usage/aliases and durable sanitized journals; no retries. Missing terminal, delta-only fallback or non-SSE JSON do not qualify as completed_nonempty.
- Passed native runner --dry-run: 24 requests, 196608 maximum generated tokens, native_sse transport, manifest SHA256 345af0d34df0d741d0b76eabe2af33af33118bb0c042b281fd7e65c3aa371ed4

## Remaining concerns

- The shared runner does not enforce this pilot recurrence gate or separate Git freeze by itself. Root must verify the independent gate and freeze before issuing the inference command; analyzer is planned to check an explicit gate receipt and freeze evidence.
- Analyzer followup review passed with 41 independent synthetic self-test checks. Its final hash must be pinned in protocol.json, and the prereview protocol hash refreshed before freeze. Capture quality also requires text/event-stream and zero malformed SSE JSON frames; record these prospective rules in the protocol.
- Item bootstrap intervals condition on fixed candidate aliases, observed selections and batch contexts. They omit model rerun variation, alternative contexts, topic/article clustering and selection uncertainty. Templates are narrow and partly shared across HANS roles; item-disjoint confirmation is not a fresh-domain validation.
- Public test/evaluation releases can have been seen in training; immutable model weight revisions are not established. Requested/returned aliases and exact source provenance limits must remain visible.
- Original PAWS annotations can be imperfect or approximate for mutual entailment; P-19 is prospectively flagged and remains in all primary denominators.
- Canonical PAWS GCS archive was inaccessible, so original-tar byte identity is unverified. Only the pinned HF mirror bytes were checked. No broader representativeness, intrinsic benchmark defect, user harm or human adoption is established.

## Commands

Safe now; this makes no request and does not access credentials:

```bash
python paper_research_20261113/run_adaption_stream_pilot.py paper_research_20261113/consequence --dry-run
```

Only after the independent gate is met and the complete prospective materials are separately frozen:

```bash
python paper_research_20261113/run_adaption_stream_pilot.py paper_research_20261113/consequence --timeout 120 --concurrency 2
```

The reviewed analysis command below makes no model calls. Replace uppercase placeholders with the externally recorded pre-inference freeze and gate identities; protocol must pin the reviewed analyzer before freeze.

```bash
python paper_research_20261113/consequence/analyze_consequence.py --directory paper_research_20261113/consequence --freeze-commit CONSEQUENCE_FREEZE_SHA40 --freeze-time FREEZE_UTC_ISO8601 --freeze-protocol-sha256 FINAL_PROTOCOL_SHA256 --gate-sha256 GATE_RECEIPT_SHA256
```

The synthetic self-test is safe before capture:

```bash
python paper_research_20261113/consequence/analyze_consequence.py --self-test
```

## Exact current hashes

| File | SHA256 |
|---|---|
| `design.md` | `aaa04c9c6505ec5ea948d579fd8bda3740481a8d5afe60e473238d61c9c56443` |
| `protocol.json` | `bd3397182d913e6253b7219c1011accb49a28e15bded9d1e9f6ba7e7cdb47847` |
| `selection_intent.json` | `773f41fbadb7903c4bbc08dd0332d1d4fa6fa34b8c23900790f1843fe2876aaf` |
| `selected_data.json` | `cedb6b48d3954ff21ae05d92ef67728f3de0f2476b0e050d8e75d9fc00a76478` |
| `selection_manifest.json` | `8a3945299bf7c601b6a43f54dacde0a9b877b44eb092788f10fe0bd6086fa419` |
| `task_key.json` | `4674cf7b95f8d3e20d43e086930118c04c074c6a2adec023ca8b7ae27a9b84e6` |
| `manifest.jsonl` | `345af0d34df0d741d0b76eabe2af33af33118bb0c042b281fd7e65c3aa371ed4` |
| `download_and_select.py` | `25f741f4b9818ed6f801c43aefa26b241c82945df8cf5ff84b314a989a8a2d0f` |
| `source/paws_source.json` | `24f34ce35202ed3745495e61b80a133597831c99a7dd7ee66daff45bf072c7e3` |
| `source/hans_source.json` | `a100f453af9e6ee2cf6b835a756ba89327de1ea929198e5bbe243e1cec04b849` |
| `source/paws_hf_api.json` | `b3fec50cc19dad421fad7298d729d150dbfbdd365da89ddac8e5307bedac749a` |
| `source/paws_test.parquet` | `ae342ff12bb84b84b95f468abf5db6cb7c7bd578271299fe9c99be75b8132f4d` |
| `source/hans.tsv` | `c55b62feef9913070e88f38938dc2492018c945ac81f70139346472494124e79` |
| `../run_adaption_stream_pilot.py` | `c280811c5f685cdc5b254d5097946835428cd87de6ea58218de1e2cad537fe5e` |
| `analyze_consequence.py` | `5693da1c197cb988b0db67fcbfd0c446374112b6dc25aa1692c2d247eb28515d` |

## Pre-correction hashes

| Changed file | Original SHA256 |
|---|---|
| `design.md` | `c813c8d0b9f665c69f958eccdb165f5aa0fcbbffe30f446e9a34e95b28074c74` |
| `protocol.json` | `84aa1e5d1741316af6decd490dffd83e2f3e146a4c351af5d8d9e6c541b9bf1e` |
| `manifest.jsonl` | `ff2051e5795da5c378e06341774c2c1a5d0c38ac13bb7bb9aed90bb01b5243dc` |
| `download_and_select.py` | `b6d0525367dacefc381c39eec3f72f27587f18fdbb7c35b549f4e986c5cad5b5` |

The selected data, task key, selection intent/receipt and pinned source bytes are unchanged. Freeze the final analyzer and prereview along with the protocol, requests, sampler and runner. This receipt intentionally excludes its own hash.

## Analyzer followup review

Read-only review and an independent rerun of all 41 synthetic checks passed. Independent linear quantile checks also matched NumPy. The review verified the strict gate receipt, frozen hashes, post-freeze capture ordering, wire/individual/aggregate/terminal/text consistency, complete-output requirement, ties, signed confirmation consequence and fixed-winner stratified bootstrap.

The author resolved three findings before this hash: pin the actual executing analyzer, retain API failure metadata before early audit returns, and remove an unregistered exact returned-alias exclusion. Gate judgments and Git commit identity remain externally attested; actual study outputs were not read. Final analyzer hash: `5693da1c197cb988b0db67fcbfd0c446374112b6dc25aa1692c2d247eb28515d`.
