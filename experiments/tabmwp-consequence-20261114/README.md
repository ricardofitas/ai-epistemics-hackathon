# Targeted TabMWP consequence audit

Read [REPORT.md](REPORT.md) for findings and [PROTOCOL.md](PROTOCOL.md) for the frozen primary analysis and the explicitly retrospective extension. The study is private research outside the manuscript.

The inputs are pinned public files from `lupantech/PromptPG`, revision `869bae8ffb8288ccc3102293b3090ec2aa17f618`. `acquisition.json` lists exact Git blob SHAs. Large source files are downloaded, not copied into this repository. `acquire.py` authenticates them before reuse.

From this directory, with Python and NumPy installed:

```bash
python acquire.py
python headline_preflight.py
python analyze.py
python -m unittest discover -s . -p test_context.py
python context_sensitivity.py
python verify.py
python build_report.py
```

The analysis uses the earlier study at `../tabmwp-archive-audit-20261114` as a regression comparator; `--prior-dir` can select a materialized copy. Local scratch execution used `--prior-dir ../snapshot`.

The official small evaluation modules are imported without invoking provider entrypoints. The GPT-3 normalization function is extracted unchanged from its source AST to avoid importing provider dependencies; this is bounded offline replay, not a full framework run. `np.argmax` calls and random fallback candidate sets are traced. Original archived outcomes are retained for stochastic paths; their broader uncertainty is checked separately.

`results/headline-preflight.json` retains the unsupported zero-shot-CoT archive, and `results/initial-stop.json` records the first parser mismatch. No model or judge API calls are made. No score is represented as human gold. Large context witnesses and permutation ledgers are retained as deterministic gzip files; the scripts regenerate their uncompressed JSON versions locally.
