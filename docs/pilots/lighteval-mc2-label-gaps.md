# Lighteval TruthfulQA MC2: actual label gaps and real-likelihood replay

Checked and executed 2026-11-12. This is a reproduction and extension of the **known** [issue #1442](https://github.com/huggingface/lighteval/issues/1442) / [PR #1444](https://github.com/huggingface/lighteval/pull/1444), not a new defect discovery. PR #1444 was opened 2026-10-20 and remained open/unmerged. The current checked main commit is `b97a6533bec22c4184b88526366fdf5d73d502c9`.

## Exact code and scope

The [metric](https://github.com/huggingface/lighteval/blob/b97a6533bec22c4184b88526366fdf5d73d502c9/src/lighteval/metrics/harness_compatibility/truthful_qa.py) (Git blob `d8cbc36625d15e62c9f35236c36c9967ceb31f17`) locates the first contiguous run of gold MC2 answer indexes and passes its endpoint as a prefix split to `mc2()`. That helper then treats every option before the split as true and every later one as false. True answers after a gap are therefore omitted. The source itself contains a comment acknowledging this limitation.

The [task adapter](https://github.com/huggingface/lighteval/blob/b97a6533bec22c4184b88526366fdf5d73d502c9/src/lighteval/tasks/tasks/truthfulqa.py) (blob `f517f049e49d4fcada263a7c59f595177876678e`) preserves the supplied choice order and derives `gold_index` directly from the labels. It does not sort true answers to a prefix. The active `truthfulqa:mc` task connects that adapter and metric.

The intended MC2 score is normalized probability mass on **all** true labels. No assessment of whether the benchmark's truth labels are semantically correct is needed for this implementation audit.

## Pinned real-dataset scan

I downloaded the actual [HF multiple-choice validation parquet](https://huggingface.co/datasets/truthfulqa/truthful_qa/resolve/741b8276f2d1982aa3d5b832d3ee81ed3b896490/multiple_choice/validation-00000-of-00001.parquet) at dataset revision `741b8276f2d1982aa3d5b832d3ee81ed3b896490`. Its SHA256 is `23f08e230ca4ed66babf3a72419af7cbde1f3d734dd396ac4cf6d088bd162afd`.

**2 of 817 unmodified records have non-prefix true labels**, at zero-based indexes 25 and 208. The historical source comment mentions row 371; the current rows are different. The previously published issue checked rows 300–399 without locating the historical example; our full current scan finds the actual affected records elsewhere.

| Row | Original MC2 labels | Unchanged metric under uniform constructed likelihoods | Correct mass under those same likelihoods |
| --- | --- | ---: | ---: |
| 25 | [1,1,1,0,1,0,0,0,0] | 3/9 = .333333 | 4/9 = .444444 |
| 208 | [1,1,0,1,0,0,0] | 2/7 = .285714 | 3/7 = .428571 |

These uniform vectors are a simple controlled proof using **real unmodified labels**, not observed model outputs. A separate semantics-preserving permutation test moves one false choice before all true choices while retaining every answer/label pair. It changes the uniform score incorrectly on 817/817 rows. This tests order invariance; it is not the incidence on the original-order dataset.

`audit_labels.py` executes the unchanged adapter function and metric class extracted with Python AST, omitting unrelated framework imports. Namespace substitutes provide data containers/base class only; no scoring logic is rewritten. It uses NumPy 2.3.5 and pyarrow to read the pinned parquet. `results.json` records the full scan.

## Replay using actual public model likelihoods

The sibling trace audit downloaded every English `truthfulqa_mc2.jsonl` file from [benchpress/sft-eval-results](https://huggingface.co/datasets/benchpress/sft-eval-results), revision `2b09f71e86d98b20fc3ef145b57fd56e9adb963f`: three SFT model families × five checkpoints, 15 files × 817 records = 12,255 item evaluations. Each trace is content-hash checked against the download manifest.

I replayed their original MC2 per-choice log-likelihoods and labels through the pinned Lighteval adapter/metric. Dummy values fill only the unused MC1 likelihood slice; they cannot affect MC2. Every document across all 15 files matched the same reference document, and all 817 reference documents matched the pinned current parquet exactly.

The inputs come from real inference, but this is a **cross-implementation metric replay**, not a reproduction of native Lighteval prompting/inference and not a correction of the published harness scores. The original harness uses labels correctly and is not affected by this Lighteval gold-gap defect.

Results:

- 28/12,255 replayed item scores differ from the correct all-label calculation by more than `1e-12`. The other two omitted true-answer masses are below that numeric threshold; the same two structural label-gap rows recur across all checkpoints.
- Maximum per-item difference: `0.0015162200632126272` on the 0–1 scale (**0.151622 percentage points**).
- Maximum mean difference over a complete 817-question checkpoint: **0.00018558385117550813 percentage points**.
- The ordering of the 15 replayed checkpoint means does **not** change.

Thus the implementation failure reaches actual dataset records and actual captured model likelihoods, while its measured effect is very small in this trace collection. Large uniform/permutation stress-test effects should not be conflated with these small observed-input replay effects.

`replay_real_likelihoods.py` and `real_replay_results.json` preserve all per-file results and affected-row likelihoods. The replay expects the trace audit's `download_manifest.json` and data files in the neighboring `mc2_real_traces` directory. The checked command-line versions use explicit paths and verify both pinned source hashes. With NumPy 2.3.5 and pyarrow installed, run:

```bash
python3 scripts/audit_lighteval_mc2_labels.py /path/to/pinned-sources /path/to/validation.parquet --output labels.json
python3 scripts/replay_lighteval_mc2.py /path/to/pinned-sources /path/to/trace-audit --output replay.json
```

The source directory must contain the two linked files named `truthful_qa.py` and `truthfulqa_task.py`. The parquet scan downloads the pinned dataset if its path is absent. Use the shared public-trace downloader from the underflow audit for the trace directory. No model weights or new inference are required. The coordinator reran both command-line scripts and reproduced the original outputs exactly; an independent agent review separately checked the dataset, likelihoods and all-label formula.

## Interpretation for the project

This is a source-backed known-positive case for testing whether research assistants inspect evaluation implementations, label semantics and answer-order invariance before asserting validity. The exact original model prompts/likelihoods are archived in the public trace data, and the evaluator source is pinned. The findings establish scorer behavior and a small conditional replay consequence. They do not establish a new flaw, large practical damage, changed published leaderboards, or an observed wrong recommendation by an assistant.
