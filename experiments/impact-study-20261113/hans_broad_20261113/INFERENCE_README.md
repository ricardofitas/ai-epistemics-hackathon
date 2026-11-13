# Frozen public-model inference on HANS600

The source-only HANS600 selection was frozen at commit `d5a3e4ca5230a454be097c6f14d6e9e81c1922a4` before inspecting the initial WSC model predictions. This extension uses the same four pinned public NLI weights and CPU environment as `../local_nli_20261113/`; it does not change that cohort's protocol or predictions. `inference_plan.json` fixes the 600 items, candidate order, binary mapping, result summaries, and 10,000-draw stratified subcase bootstrap before HANS600 inference.

Run from the workspace root. The source-only preflight checks the exact source hashes, original model-source receipt, all four model snapshots and prior HANS80 nonoverlap, without loading a model or producing predictions:

```bash
.venv-nli/bin/python experiments/impact-study-20261113/hans_broad_20261113/run_broad_nli.py --preflight
```

After publishing **this** inference plan, runner, analyzer and README as a new Git commit, supply the published commit UTC timestamp and exact file hashes:

```bash
.venv-nli/bin/python experiments/impact-study-20261113/hans_broad_20261113/run_broad_nli.py --run \
  --freeze-commit <40-hex-commit> --freeze-time <UTC-ISO-8601> \
  --freeze-plan-sha256 <published-inference-plan-sha256> \
  --freeze-broad-protocol-sha256 f8da17431a8b3d57f5e64465f79077c2276d737ddd44479daec0d3ce94966842 \
  --freeze-runner-sha256 <published-runner-sha256>
.venv-nli/bin/python experiments/impact-study-20261113/hans_broad_20261113/analyze_broad_nli.py
```

The runner sends premise/hypothesis only and writes 600 three-way labels plus raw logits per model. It refuses to resume or overwrite outputs. The analyzer requires four complete pinned receipts, loads the initial WSC analysis only after prediction and recomputes both WSC selection winners from its frozen scores. A tied original winner yields no selected-winner contrast. It reports every candidate, macro/micro accuracy, the six heuristic × gold cells, three heuristics, the signed fixed-winner contrast, and a paired subcase resampling interval.

This is a broader slice of the same publicly available HANS benchmark, not an independent benchmark. Model pretraining exposure is unknown; templates within subcases remain dependent. An observed HANS600 contrast cannot certify the WSC's curated NLI interpretations or a real user's model choice.
