# TruthfulQA MC2: bounded audit of public model likelihood traces

Audit date: 2026-11-12. Result: **no material original-versus-stable scoring differences in 12,255 archived item-run rows**. This is a negative incidence check on third-party model outputs, not a new model experiment or a population prevalence estimate.

## Source and selection

Source: [benchpress/sft-eval-results](https://huggingface.co/datasets/benchpress/sft-eval-results/tree/2b09f71e86d98b20fc3ef145b57fd56e9adb963f), revision `2b09f71e86d98b20fc3ef145b57fd56e9adb963f`. Its [dataset card](https://huggingface.co/datasets/benchpress/sft-eval-results/blob/2b09f71e86d98b20fc3ef145b57fd56e9adb963f/README.md) identifies MIT-licensed swiss-ai-fork lm-evaluation-harness outputs for three Tulu3-SFT model families, five checkpoints each, with a Tulu3 chat template and vLLM backend. These model outputs were released by the dataset authors; this audit does not rerun those models.

The bounded selection includes **every file ending exactly `/truthfulqa_mc2.jsonl` in the pinned repository tree**, excluding translated task files. This yields 15 English files: llama3.2-1b-sft, qwen2.5-1.5b-sft, and smollm2-1.7b-sft, each at steps 165, 990, 1980, 2805, and 3667. Each file has 817 rows on the same 817 distinct question texts. Download size: 85,866,026 bytes. `download_manifest.json` records each pinned URL, Git object ID, byte size, and SHA256.

The JSONL contains per-choice `(log_likelihood, is_greedy)` tuples in `filtered_resps`, matching true/false labels in `doc.mc2_targets.labels`, the prompts, and the logged `acc`. The scanner checks shapes and binary labels before re-scoring.

## Executed comparison

The scanner executes the **unchanged pinned `process_results_mc2` body** from EleutherAI/lm-evaluation-harness commit `d6de81643928d653435c431bae19945d41d32520`, checking source SHA256 `d3c827d1e2cd442a1e4738b527a18effd48cbb2aed478c12a652311b5ea4dbc8`. It compares that function with max-shifted normalized true-answer probability under NumPy 2.3.5. This applies the audited current scoring function to the archived likelihoods; the archive itself used a swiss-ai fork.

| Quantity | Result |
| --- | ---: |
| Files / related model checkpoints | 15 |
| Distinct question texts | 817 |
| Item-run rows | 12,255 |
| Candidate likelihoods | 88,230 |
| Nonfinite likelihood rows | 0 |
| Nonfinite upstream scores | 0 |
| Absolute upstream–stable difference > 1e-12 | 0 |
| Maximum absolute upstream–stable difference | 5.55e-16 |
| Maximum absolute recomputed–logged score difference | 2.22e-16 |
| Maximum absolute aggregate-mean difference | 5.55e-17 |
| Ordering of 15 aggregate means | unchanged |

The minimum individual likelihood was −79.9891. More relevant to a normalization-wide underflow failure, the minimum across rows of the **maximum candidate likelihood** was −38.3594. No row had its maximum candidate likelihood below −700. The archived examples therefore stay far from the finite-input underflow range used in the controlled reproduction.

Full per-file denominators, score means and numeric diagnostics are in [`audit_results.json`](../../results/pilots/truthfulqa-mc2-real-traces-20261112/audit_results.json). The coordinator independently reran the complete audit with identical results and independently redownloaded a pinned source file to verify its checksum. An empty `material_rows` array records that no rows exceeded the stated tolerance; no failed or nonfinite rows were silently dropped.

## Reproduce

Obtain the pinned scorer `utils.py` linked in the existing MC2 audit. Then run:

```bash
python3 scripts/download_mc2_real_traces.py results/pilots/truthfulqa-mc2-real-traces-20261112/download_manifest.json /path/to/trace-audit
python3 scripts/audit_mc2_real_traces.py /path/to/trace-audit /path/to/pinned-utils.py
```

The downloader verifies all 15 source checksums and can resume from matching local files. The scanner verifies source and data checksums before analysis. The 85.9 MB source traces should be downloaded from their pinned public host rather than copied into the research repository.

## Interpretation

The controlled finite-input MC2 defect remains reproducible, but **this real-trace sample provides no observed practical score impact**. Its 12,255 rows are repetitions of 817 questions across three small model families and related training checkpoints, selected for public availability. They are not independent research cases and do not establish a general zero-failure rate for models, languages, inference routes, or longer continuations. Conversely, the stress test does not establish practical prevalence.

Given this negative result and separately identified prior fixes for the same numerical mechanism, this case is best retained as an implementation robustness/control example unless affected real traces can be obtained. It is weak as the project's main new scientific finding. A separate model-recommendation experiment still needs to measure whether an assistant endorses an evaluation that fails the stated research requirement.
