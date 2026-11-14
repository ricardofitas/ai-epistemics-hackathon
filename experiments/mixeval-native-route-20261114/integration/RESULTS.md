# MixEval ordinary native-route integration

The two positive replay groups completed once after protocol commit
`0e2616f099b5f5defb395f3d545b3736c23b063a`. No new model calls or
response generation occurred. Existing matched public outputs were replayed at
a local serving boundary.

| Group | Original source rows | Scored rows | Official rule successes | Local rule mean | Captured-serving batches |
| --- | ---: | ---: | ---: | ---: | ---: |
| Free-form | 17 | 17 | 13 | 0.7647058823529411 | 1 |
| Multiple-choice | 32 | 32 | 20 | 0.625 | 1 |

These scores describe the same previously observed responses. The new evidence
is successful passage through the complete imported native `run_eval`,
generator `run`, evaluator `run`, and `FileStorage` path with explicit source
and output coverage checks.

The full native files were imported normally. No native method was extracted
through AST. The environment lacks installed One-Eval/DataFlow and their heavy
model dependencies. Package export facades and documented inert dependency
sentinels enabled the import. Zero forbidden optional-dependency calls occurred.

Explicit interventions replace provider initialization with local captured
serving, bind the source-specific official prompt constructor, replace two
per-task evaluator scoring methods with the verified official rule adapter, and
bypass the incompatible native choice post-rescore. The official rule helper
adapter still uses bounded exact-helper AST loading. Its original alias
counterexamples and random fallback remain unchanged.

Both native diagnostic denominators equal the complete nominal group size.
Native returned statistics preserve the original diagnostic role and
`display_as_primary=false`. Their legacy metric strings remain
`any_math_verify` and `parse_choice_acc`; those labels do not describe the
replaced official rule scoring boundary. The integration report explicitly
records the actual official-rule mode. The One-Eval primary metric stage was
not executed.

The MC group retains five official random-fallback outcomes with the frozen
seed42 and preserved row order. Empty/unparseable outputs were not silently
forced incorrect or removed from the denominator. The row-level captures keep
every parsed outcome, score, source hash, response hash and random draw.

All27 frozen implementation/input files remain byte-identical after execution.
See `EXECUTION_RECEIPT.json`, `FROZEN_IMPLEMENTATION.json`,
`VENDORED_MODULES.json`, and each group `RESULT.json`. Independent coverage
controls and result reconciliation are maintained by the separate reviewer.

This is a bounded full-module integration replay. It does not establish a full
installed distribution, model/tokenizer/remote transport behavior, default
MixEval model-judge accuracy, an official full-benchmark score, or an externally
affected conclusion.
