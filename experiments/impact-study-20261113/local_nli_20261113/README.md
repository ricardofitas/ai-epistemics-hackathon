# Exploratory local NLI WSC → HANS pilot (2026-11-13)

This is a **new public-model cohort**, separate from the earlier offline proxy study and the unexecuted Adaption aliases. Four public cross-encoder three-way NLI models are pinned in `protocol.json` by Hugging Face revision and model-weight SHA-256. The already frozen WSC and HANS task inputs are reused byte-for-byte. Model inputs are only ordered premise and hypothesis strings; labels, analysis role and source metadata are not passed to the classifiers.

## Design and endpoints

Each candidate receives the same 144 WSC classification tasks (two hypotheses for each of 72 passages) and 80 HANS tasks. The WSC selection split has 35 passages from 20 source families; the separate confirmation split has 37 passages from 21 other families. The WSC *imposed* paired score counts an entailment prediction for the gold replacement and a contradiction prediction for the non-gold replacement. The *repaired* score permits either neutral or contradiction for the latter. This recast is conditional on the selected coreference interpretation; it does **not** establish human-certified three-way NLI gold.

The highest raw paired count in WSC35 selects a candidate under each rule. All ties and all six pairwise orderings are reported. If both winners are unique, compare the two fixed winners on repaired paired accuracy in independent WSC37 and binary accuracy in HANS80. A zero or negative difference remains a result. The source-family WSC and template-cluster HANS bootstrap intervals condition on the fixed candidate set and selection. The 80 HANS cases cover only lexical overlap: three templates, with non-entailment confined to one template and entailment to two. Template and label are confounded, so a three-cluster interval is only descriptive sensitivity and cannot establish generalization. Prior exposure of HANS by a pretrained model is unknown.

This raw-count winner rule is an exploratory abstraction, not the full earlier advice policy with significance tests and macro-F1. A positive independent difference would be evidence within this cohort, not a replication of the Adaption result or a GAMMAF-level claim. Human WSC semantic validation and broader external replication remain pending.

## Source-only preparation

From the workspace root, after installing the pinned CPU dependencies in `.venv-nli`, run:

```bash
.venv-nli/bin/python experiments/impact-study-20261113/local_nli_20261113/run_local_nli.py --prepare-sources
.venv-nli/bin/python experiments/impact-study-20261113/local_nli_20261113/run_local_nli.py --preflight
.venv-nli/bin/python experiments/impact-study-20261113/local_nli_20261113/analyze_local_nli.py --self-test
sha256sum experiments/impact-study-20261113/local_nli_20261113/{protocol.json,run_local_nli.py,analyze_local_nli.py,source_receipt.json}
```

`--prepare-sources` accepts already downloaded model snapshots only when each Hugging Face download metadata record matches the pinned commit. It checks every model file, the weight hash, three-way label mapping, and the frozen task files, then writes `source_receipt.json` once. If the model directory is absent it downloads the exact pinned revision. `--preflight` rechecks those bytes and emits `inference_calls: 0`; neither mode loads the model or writes predictions. A changed source or protocol requires a newly named cohort, rather than overwriting a receipt.

## Frozen run and analysis

After externally publishing a Git freeze commit containing the protocol, runner, analyzer and source receipt, supply its real commit, UTC time and the published hashes to the runner:

```bash
.venv-nli/bin/python experiments/impact-study-20261113/local_nli_20261113/run_local_nli.py --run \
  --freeze-commit <published-40-hex-commit> \
  --freeze-time <published-UTC-ISO-8601-time> \
  --freeze-protocol-sha256 <published-protocol-sha256> \
  --freeze-source-sha256 <published-source-receipt-sha256> \
  --freeze-runner-sha256 <published-runner-sha256>
.venv-nli/bin/python experiments/impact-study-20261113/local_nli_20261113/analyze_local_nli.py
```

The CPU runner checks hashes and version pins, uses `eval()` and `torch.inference_mode()`, batch size 8, four CPU threads, full untruncated tokenization, and argmax of three raw float32 logits. It fails if a sequence exceeds the architecture limit. It writes 224 rows and a hash receipt per model. Partial failures remain visible; the runner refuses to resume or overwrite a prediction directory. The analyzer requires all four complete, pinned outputs, verifies each receipt and prediction set, then writes `analysis/summary.json` plus passage-level and HANS-level scores once. Do not interpret partial output as a full cohort result.

The model snapshots are approximately 2 GB in total and should be kept as local source evidence, not committed with study text. The freeze commit should identify the lightweight source receipt and protocol hashes; model bytes remain independently pinned by SHA-256 and Hugging Face commit metadata.
