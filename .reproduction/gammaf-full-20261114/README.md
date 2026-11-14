# Pinned full GAMMAF team reproduction

Preparation only: no model calls, no judge calls, no live workflow launch by this subtask.

Root should create `ricardo/gammaf-full-reproduction-20261114` from Antonio's exact commit `d4419f160252adee3d639df9ea23cd1600277c32`. Place this capsule's files under `.reproduction/gammaf-full-20261114/`, except the workflow, which belongs at `.github/workflows/gammaf-full-reproduction-20261114.yml`. Commit preparation and protocol before a separate `LAUNCH.json` push. The teammate branch, main, and frozen `artifacts/results.json` remain untouched.

The runner checks pinned original code, results and terminal projection. It retrieves the 28 raw trajectory JSON files at public upstream commit `53be3249ebfa631d8e960c9fb1c931d526654697`, checks every exact byte count and Git blob SHA, parses only authenticated bytes, and places them at the paths expected by the unchanged loader. The trajectory total is **111,232,152 bytes**; the source manifest's separate summary JSON is not needed by the loader and is not downloaded. There is one HTTP attempt per missing file, no redirect, no retry, and a global 900-second bootstrap/test/full-run deadline.

The runner applies the previously reviewed shadow population accounting patch only in this derivative checkout, runs the complete 33 original plus five focused regression tests, and invokes the unchanged full experiment runner with all experiments, 10,000 bootstrap draws, fixed seed, and figures disabled. NumPy, SciPy, Matplotlib and pytest are pinned. No model credentials or model endpoint is used or supplied to the workflow.

Comparison retains the original scientific scope: existing archived conversations and offline terminal reaggregation. It checks clean/theory outputs, guard tuning, full/held-out rows, cells, strata, verdict and task differences; inferential statistics equality is separately reported to expose dependency-version sensitivity. The shadow classifications and per-population/per-cell rates should match; only the erroneous mixed-population global rate and mean should change. The corrected combined rate is 540/6859, while detector and control rates retain 217/5518 and 323/1341.

The source receipt, test JUnit/logs, full output tables/JSON and comparison are preserved in a bounded GitHub artifact. The 111 MB raw cache stays ephemeral on the runner; exact public retrieval provenance is retained. Successful source authentication closes the previous missing-input blocker, but it does not turn retrospective holdout results into a prospective experiment or demonstrate causal message transmission.

Offline validation of the new download boundary:

```sh
python3 .reproduction/gammaf-full-20261114/test_bootstrap.py
```

Full root-controlled launch uses the workflow's existing Actions event. Do not rerun a failed job blindly; inspect `STOP.json` and source/test receipts first. Preparation of this capsule has made zero network source downloads and zero model calls.
