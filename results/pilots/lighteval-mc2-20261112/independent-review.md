# Independent review: known Lighteval TruthfulQA MC2 label-gap defect

Reviewed 2026-11-12. **Confirmed with bounded interpretation.** The candidate describes a real defect in the pinned scorer and a small consequence when archived public likelihoods from another harness are passed through that scorer. It is a reproduction of known issue [#1442](https://github.com/huggingface/lighteval/issues/1442) and proposed fix [PR #1444](https://github.com/huggingface/lighteval/pull/1444), not a new discovery. This review made no GitHub changes and performed no new model inference.

## Source verification

Independent read-only GitHub API requests confirmed main commit `b97a6533bec22c4184b88526366fdf5d73d502c9` and the following exact source blobs. Local Git blob hashes match the GitHub responses byte-for-byte.

| File at pinned commit | Verified Git blob |
| --- | --- |
| [Metric: `src/lighteval/metrics/harness_compatibility/truthful_qa.py`](https://github.com/huggingface/lighteval/blob/b97a6533bec22c4184b88526366fdf5d73d502c9/src/lighteval/metrics/harness_compatibility/truthful_qa.py) | `d8cbc36625d15e62c9f35236c36c9967ceb31f17` |
| [Adapter: `src/lighteval/tasks/tasks/truthfulqa.py`](https://github.com/huggingface/lighteval/blob/b97a6533bec22c4184b88526366fdf5d73d502c9/src/lighteval/tasks/tasks/truthfulqa.py) | `f517f049e49d4fcada263a7c59f595177876678e` |

The adapter preserves answer order and obtains gold indexes from the supplied labels. The scorer finds the first contiguous run of MC2 gold indexes, converts its endpoint into a prefix split, and sums probability mass on that prefix. On the two original-order affected rows, one later true option is consequently placed in the false partition. The denominator still includes every choice; the missing numerator mass is the failure.

I also inspected the pinned metric registration: `truthfulqa_mc_metrics` uses `TruthfulqaMCMetrics()` and averages MC2 with `np.mean`. The task connects to this registration. The pinned `Doc` and `ModelResponse` are data containers without a constructor transformation that repairs label order or transforms `logprobs`. Thus the extracted-method execution accurately tests this scoring path, while remaining an isolated scorer test rather than an execution of the entire framework.

PR #1444 was independently confirmed open and unmerged (`merged: false`, `merged_at: null`), created 2026-10-20. Its title, description and linked issue identify this same gap/order-invariance mechanism. The source itself already acknowledges the limitation.

## Reproduction and dataset incidence

I reran both supplied scripts and wrote a separate checker, `independent_check.py`, with its own label-mask reference using max-shifted exponentials and `math.fsum`. The checker runs the unchanged source class and adapter extracted by AST. Only framework containers/base class are substituted; the scoring logic is not reimplemented on the tested side.

The minimal controlled example `[1,0,1]` with probabilities `[.2,.3,.5]` gives actual `.2` and correct `.7`. Permuting the same answer/label/likelihood triples into `[1,1,0]` makes the actual score `.7`. This is a conditional scorer order-invariance failure; it does not claim that model likelihoods themselves would remain constant under a new prompt or answer order.

I independently downloaded the [pinned HF parquet](https://huggingface.co/datasets/truthfulqa/truthful_qa/resolve/741b8276f2d1982aa3d5b832d3ee81ed3b896490/multiple_choice/validation-00000-of-00001.parquet), revision `741b8276f2d1982aa3d5b832d3ee81ed3b896490`. Its 271,033 bytes have SHA256 `23f08e230ca4ed66babf3a72419af7cbde1f3d734dd396ac4cf6d088bd162afd`, matching the local file.

**Exactly 2/817 original unmodified rows have non-prefix MC2 gold labels:**

| Zero-based row | Labels | Omitted true index | Uniform actual | Uniform correct |
| --- | --- | ---: | ---: | ---: |
| 25 | `[1,1,1,0,1,0,0,0,0]` | 4 | 3/9 | 4/9 |
| 208 | `[1,1,0,1,0,0,0]` | 3 | 2/7 | 3/7 |

All rows have one MC1 gold at index zero, so the original-data finding is not caused by a violation of the scorer's separate MC1 assumption. I also reproduced the supplied 817/817 uniform false-first permutation failures. Those are constructed stress-test incidence, not the original dataset incidence or observed model score impact.

## Archived-likelihood replay

The 15 input files are pinned to `benchpress/sft-eval-results` revision `2b09f71e86d98b20fc3ef145b57fd56e9adb963f`. Independently checked each local trace's byte count, SHA256 and Git blob hash against the download manifest. All 15 files contain exactly the same 817 document IDs, and every complete `doc` object equals the pinned parquet row at that ID. Every candidate likelihood is finite and has the expected shape.

These are archived inference likelihoods from a different harness. Passing their original MC2 likelihoods and labels through the pinned Lighteval scorer is a **cross-implementation scoring replay**, not native Lighteval prompting/inference. MC1 placeholders occupy only the distinct MC1 slice; they cannot affect the MC2 result. Correct all-label reference scores match each archive's logged `acc` within `1e-12`, so this is not evidence that the archive's published scores suffered the Lighteval defect.

| Quantity | Independently verified result |
| --- | ---: |
| Original distinct questions | 817 |
| Related checkpoint files | 15 |
| Item-run rows | 12,255 |
| Structurally affected gap row/checkpoint pairs | 30 |
| Absolute actual–correct differences greater than `1e-12` | 28 |
| Maximum item difference, 0–1 scale | 0.0015162200632126272 |
| Maximum item difference, percentage points | 0.15162200632126272 |
| Maximum 817-question mean difference, percentage points | approximately 0.000185584 |
| Ordering of 15 checkpoint means changed | No |

The distinction between 30 and 28 matters. The same two gap rows appear in all 15 files, and an independent 80-digit Decimal calculation confirms positive omitted true mass on all 30. Row 25 at qwen2.5 step 990 omits approximately `9.12335e-13`; row 25 at smollm2 step 990 omits approximately `7.94118e-13`. Both lie below the stated threshold. Therefore “28 scores differ by more than `1e-12`” is accurate; “only 28 scores are mathematically affected” would be inaccurate.

The supplied and independent mean-difference calculations agree to meaningful precision. Their last few digits differ because one subtracts floating-point aggregate means and the other sums paired differences with `math.fsum`. This is immaterial to the small measured effect. The maximum difference on structurally unaffected rows is `4.44e-16`, consistent with rounding differences in the independent reference.

## Assessment

The candidate's principal numerical and source claims are supported. The useful extension beyond the existing issue is finding the two affected rows in the actual pinned dataset and quantifying a small conditional effect on available real inference inputs. The existing writeup correctly distinguishes constructed likelihood tests, original label incidence, and public archived-input replay.

Retain these limits in any final report: known defect; no native Lighteval model experiment; no correction to the originating harness's published scores; no changed checkpoint order here; no estimate of independent-population prevalence from 15 related checkpoints; no observed mistaken assistant recommendation. The large uniform/permutation effects cannot be substituted for the much smaller measured archived-input effects.

Reproduction command from the workspace root:

```bash
PYTHONPATH=mc2_prior_art/lighteval/deps python3 lighteval_verify/independent_check.py
```

Artifacts: `independent_results.json` contains detailed independent per-file and per-gap-row results; `upstream_checks.json` records the independently retrieved GitHub metadata.
