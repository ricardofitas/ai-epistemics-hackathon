# HANS600 broader external holdout (source-only freeze)

This is a prospective **separate external follow-up** for the local public-model WSC pilot. It was sampled by source-only rules before inspection of any of that cohort's model predictions. It is not part of the original 224-task/model run; it needs its own frozen inference runner and result receipt. It does not repair or replace the earlier HANS80 result.

The official HANS evaluation source at pinned commit `7299f6f657089ce06a0f98e7e81f8d0f5b7741ce` has 30,000 rows in 30 subcases. The deterministic script selects 20 per subcase, excluding every HANS80 pair ID and every exact HANS80 premise/hypothesis pair. The 600 rows cover all three heuristics (200 each), both binary labels (300 each), all 30 subcases and 58 templates. Each heuristic-by-label stratum has 100 cases. Source SHA-256, data SHA-256, sampling seed and candidate set are pinned in `protocol.json`.

To regenerate into a separate directory from the 15.5 MB official source file:

```bash
python prepare.py --source heuristics_evaluation_set.txt --output-dir /tmp/hans600-check
sha256sum /tmp/hans600-check/{selected_data.json,task_key.json}
```

The source can be downloaded from `https://raw.githubusercontent.com/tommccoy1/hans/7299f6f657089ce06a0f98e7e81f8d0f5b7741ce/heuristics_evaluation_set.txt`; verify its SHA-256 before using it. The selected data has analysis labels but a model must receive only premise, hypothesis and an opaque task ID.

If the original WSC35 imposed and repaired rules each select a unique candidate, their identities are fixed before the HANS600 scores are inspected. The primary contrast is the repaired-selected candidate's binary accuracy minus the imposed-selected candidate's binary accuracy, averaging across the 30 subcases. The preregistered interval is a paired bootstrap over subcases within the six heuristic-by-label strata. All candidate scores and a zero or negative contrast remain visible.

HANS600 is broader than HANS80, but still comes from the same public HANS corpus. Template dependence and unknown pretraining exposure limit claims of generalization or novelty. A successful HANS600 difference remains an exploratory external test, not evidence of an actual user decision or a complete reproduction of the original advice policy.
