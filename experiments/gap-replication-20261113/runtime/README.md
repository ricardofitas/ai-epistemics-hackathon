# Prospective source-disjoint performance-gap study runtime

These files prepare and analyse a separate frozen study. They make no model calls
except when the separately pinned native-SSE runner is explicitly invoked by the
one-shot execution wrapper. Prior frozen math30 files are unchanged.

The source cohort contains exactly 30 first-double-pass source families, all in
one replication role, with four released variants: numerical substitution,
paraphrase, P1 instance0 and P1 instance1. Every model/variant uses the same ten
blocks of three unrelated families. The fixed pair is Gemma and DeepSeek; it was
chosen to replicate the prior pilot's observed pair. This study does not repeat
the original P1/P2 mixture or infer isolated effects of added reasoning clauses.

The primary signed contrast compares the DeepSeek–Gemma accuracy gap between
P1 instances and the target transformations. Sharp finite-cohort bounds retain
unknown correctness in [0,1]. Meaningful replication requires the exact lower
bound to be at least 1/10; positivity alone requires lower>0. These are prespecified
finite-cohort rules, not population confidence claims. Primary definitions and
all source dispositions must be pinned before new solver outputs exist.

The scoring codec and format-only admission code are byte-identical copies of
the previous pilot. Capture replay changes the fixed trial prefix to GR. One
strict whole JSON answer is required; invalid captures or formats remain unknown.
Explicit ABSTAIN is a known zero. No retries, repairs, replacement models, family
additions or automatic resumption are allowed.

Offline verification:

    python -m unittest discover -s experiments/gap-replication-20261113/runtime -p 'test_*.py'

Prepare only after the source-review gate passes:

    python prepare_manifest.py --selected-data selected_data.json --source-manifest source_manifest.json --source-disposition source_disposition.json --selection-plan selection_plan.json --primary-spec primary_spec.json --prospective-design prospective_design.md --runner /path/to/scripts/run_adaption_stream_pilot.py --output-dir /new/study/directory

After the frozen single execution, replay raw evidence with capture_math.py and
its required external commit/time/protocol digest. Then run:

    python analyze_gap.py --directory /path/to/captured/study

Raw capture, prediction rows, primary summary and exploratory/descriptive
secondaries are distinct files. Reanalysis outputs are exclusive; copy inputs to
a new directory before reproducing them. All runtime code uses Python's standard
library; there are no NumPy/SciPy dependencies.
