# Installed native Harness offline integration

Completed against EleutherAI/lm-evaluation-harness d6de81643928d653435c431bae19945d41d32520 (lm_eval0.4.14.dev0). The protocol was committed before execution in research commit0ce2cb6b708e9921ac749174bb54c4ae1d527b0d.

The actual installed ConfigurableTask loads frozen local JSON through datasets, runs its zero-shot context and build_all_requests path, and scores two constructed likelihood vectors per record with native process_results. This is not an AST projection. Six installed native module files match the checkout byte-for-byte. Local data overrides are recorded in PROTOCOL.json and task CONFIG files.

Result:200 reused source units (100 ARC-Challenge,100 OpenBookQA),801 option requests,400 constructed scoring controls; no differences from the earlier projection carrier. Source-gold-positive fixtures all score1; first-non-gold-positive fixtures all score0 for acc and acc_norm. ERRORS.json is empty. Independent reconciliation passes in VERIFICATION.json.

No model backend, tokenizer, paid API or GPU execution occurred. Constructed vectors do not measure model accuracy. These are reused diagnostic data, not independent generalization or a new natural fault. Non-zero-shot rendering, remote source acquisition and model-backed evaluation remain untested.

## Reproduction

Use a new directory and virtual environment. Clone https://github.com/EleutherAI/lm-evaluation-harness and check out the exact revision above. Install the package from that checkout, using environment_freeze.txt and NATIVE_INSTALL_PROVENANCE.json for recorded dependencies. The captured environment used CPU torch2.5.1+cpu from the official PyTorch CPU wheel index. No source modifications are needed.

Keep a copy of the frozen archive before rerunning because the scripts overwrite generated outputs in their own directory. From a copied extraction, invoke the environment Python:

    python run_native_smoke.py prior /absolute/path/to/pinned/checkout
    python verify_native_smoke.py prior

The scripts set Hugging Face offline variables; all source rows and previous carrier inputs are included under prior/. The native package checkout is an explicit external source dependency. Dataset cache and installed packages are intentionally excluded. Installation logs retain operational provenance; runtime source-package paths are historical, not portable requirements.

PREVIOUS_PDF_IDENTITY_CHECK.json records a separate prior-draft byte-identity discrepancy: materialized Library PDF and pre-upload source differed in bytes but had exactly equal extracted text across6pages. The cause is not established. This is unrelated to native task execution.
