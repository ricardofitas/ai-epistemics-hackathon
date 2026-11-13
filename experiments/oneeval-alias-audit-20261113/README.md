# Registered metric aliases can change a score and reverse a comparison

This local audit pins OpenDCAI/One-Eval commit `8aba20ad17ee2c7d2391162ac03ffaebcbb17506`.
The registered names `choice_accuracy`, `accuracy`, and `acc` resolve to the exact same Python function.
On more than 100 records, `MetricRunner.run_bench` routes the two aliases through a parallel reducer while the canonical name bypasses it.
With the supported `valid_only` denominator, that reducer weights chunk scores by all rows rather than the rows counted by the metric.

The witness contains 101 constructed response records per system. A has 51 correct answers, one wrong answer and 49 abstentions. B has 76 correct and 25 wrong answers. Under the same selective-accuracy specification, A has 51/52 correctness and B has 76/101 correctness.

| System | `choice_accuracy`, two workers | `accuracy`, two workers | After the routing correction |
|---|---:|---:|---:|
| A | 98.0769% | 50.4950% | 98.0769% |
| B | 75.2475% | 75.2475% | 75.2475% |

The alias changes the reported winner. A single worker restores A's original alias score. The fixed records and metric arguments are held constant in these comparisons.

The unmodified `ScoreCalcAgent.run` method reproduces the change and writes the corresponding Step3 records. Both original invocations are reported by that agent as successfully computed. The local test supplies the original BenchInfo dataclass, an inert graph-agent base, a standard-library logger, and a simulated three-CPU host. It exercises the scoring backend without running the web server or a new LLM generation.

The proposed patch routes metrics by registered function identity. It restores alias equivalence in 60 combinations of record count, worker count and metric name, and in 20 shuffled-row checks. The fixed scoring agent also restores the witness scores. These are controlled verification combinations over constructed records.

## Scope and controls

The default `total` denominator and the dedicated `run_bench_with_contract` route pass the unaffected controls. The inspected gallery primary configurations use the canonical name. This finding concerns the supported configurable-metric route, including ScoreCalcAgent, and requires further measurement of naturally occurring affected configurations and outputs. Broad deployment prevalence and a naturally occurring model-ranking reversal remain open validation targets.

## Reproduce locally

Linux with Python 3.11 or 3.12 was the execution environment. The required metric/parser code and the small word2number dependency are included with their licenses. The scripts use the bundled sources and make no inference requests.

```bash
python3 reproduce_alias.py
python3 validate_alias.py
```

`alias_witness.json` preserves the original-name comparison. `alias_validation.json` records boundary, worker, permutation, corrected-route and scoring-agent checks. `alias_routing_fix.patch` contains the proposed local correction. `UPSTREAM_SOURCES.json` records pinned source hashes. The original source files are retained alongside the corrected runner.

This evidence is a private research checkpoint. External human validation, broader prior-art review and measurements on recorded model outputs are pending.
