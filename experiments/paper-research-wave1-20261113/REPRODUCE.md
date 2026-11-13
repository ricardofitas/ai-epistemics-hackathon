# Offline reconstruction and analysis

No API key or new inference is required. Run these commands from this experiment directory after checkout. The sampling freeze is `576bd7a1ab31024464f81368f51800b712564c14`, timestamp `2026-11-13T04:20:31Z`; first ratings were committed before coordinator analysis at `d592e6df7d8aef413ece3b3986b75f75f1b7b49e`.

## Restore exact journals

Choose a new temporary destination. The decoder verifies all original, compressed and encoded hashes. Copy the restored `study/*.jsonl` files into this experiment's `stream_journals/` directory.

```bash
python3 stream_archive/reconstruct_stream_journals.py --output /tmp/paper_wave_restored
mkdir stream_journals
cp /tmp/paper_wave_restored/study/*.jsonl stream_journals/
```

## Verify captures and reconstruct the anonymous packet

```bash
python3 methods/collect_wave.py . --freeze-commit 576bd7a1ab31024464f81368f51800b712564c14 --freeze-time 2026-11-13T04:20:31Z
```

Git commit/time are externally checked provenance inputs; the collector itself does not query GitHub. Existing packet/key bytes cannot silently change. Provider event/status mismatches remain operational incompletes.

```bash
python3 methods/summarize_wave.py . --ratings-a reviews/first_a.jsonl --ratings-b reviews/first_b.jsonl --first-review-freeze reviews/first_review_freeze.json --adjudication reviews/adjudication.json --output /tmp/recomputed_analysis_summary.json
```

Compare the recomputed bytes with `analysis_summary.json`. The helper verifies immutable first files before loading the model/repetition key. Human review remains pending.

The independent post-hoc scope/sensitivity audit is also reproducible with `methods/audit_scope_sensitivity.py`; see its `--help` for the explicit paths. It does not relabel original primary outcomes.

## Prepared future methods

Rebuild the human packet into a new directory:

```bash
python3 methods/build_human_packet.py . --plan methods/HUMAN_REVIEW_PLAN.json --output /tmp/paper_human_packet
```

Generated timestamps differ; selected IDs, texts and order are deterministic. Do not open the companion key before a first human pass. No human ratings have been obtained.

The `consequence/` folder contains a prereviewed 24-request actual-data design and analyzer. `NOT_RUN_STATUS.json` records failure of its exact PAWS recurrence gate. Synthetic parser checks and selected data are prepared methods, not model-performance findings. Inference would require valid activation evidence and a separate prospective freeze. Original PAWS archive byte identity is unverified; the prepared sample is pinned to a documented HF mirror. HANS bytes match its pinned official source.
