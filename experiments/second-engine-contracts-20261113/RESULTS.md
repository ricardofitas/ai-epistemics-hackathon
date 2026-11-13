# EvalScope native contract crosscheck — 13 November 2026

The six completed native-package audits are healthy for the tested reference,
question-dependency and deterministic row-scoring invariants. The attempted
cross-system replication of the One-Eval failures was **negative**. This narrows
the supported finding to the previously pinned One-Eval configurations; it does
not establish a general defect across evaluation engines.

| Benchmark | Native rows | Best constant response | Constant accuracy | Reference oracle |
| --- | ---: | --- | ---: | ---: |
| SciQ | 1,000 | D | 25.300% | 100% |
| WinoGrande | 1,267 | B | 50.434% | 100% |
| HellaSwag | 10,042 | C | 25.732% | 100% |
| BoolQ | 3,270 | Yes/A | 62.171% | 100% |
| MedMCQA | 4,183 | A | 32.226% | 100% |
| PubMedQA | 1,000 | YES | 55.200% | 100% |

All 20,762 source records were retained. There are 50 native scoring conditions,
including unshuffled and built-in shuffled controls. The shuffle has no effect
on free-form PubMedQA and its repeated conditions are not independent evidence.
Class imbalance explains the larger BoolQ and PubMedQA constant baselines; these
are not scoring defects. All native reference oracles score 100%. No tested
question-dependency failure occurred. Context dependency was checked for BoolQ
and PubMedQA; this is not a claim that every optional source field is required.

The SciQ corpus is especially informative: its first row has answer D, but the
full target distribution is A=250, B=250, C=247, D=253. A fixed-D hypothesis based
on the preview would have been false. Exact question joins to the prior pinned
AllenAI SciQ test source match all 1,000 rows, including the multiset of choices,
the correct answer text and support text, with no ambiguous or unmatched rows.
Its native answer positions are already varied despite `shuffle_choices=false`.
The One-Eval index collapse also does not transfer to native WinoGrande.

## What was executed

The actual unmodified EvalScope package was installed and imported in Python
3.11.18 from commit `59bb367bd8565f347266a48ac1230af0b5131b97` (package version
`0.0.0.dev0`). This scopes the result to a development commit, not every release.
The native ModelScope dataset configuration succeeded for all six panels, so no
HuggingFace fallback was needed. Full raw records, pre-format and inference-ready
Samples, native source snapshots, dependencies and per-panel logs were retained.
Dataset revision metadata is null; captured corpus bytes, not an assumed source
repository revision, identify the data used.

The script used the native converter and formatter, compared the visible loaded
prompt to native formatting, then ran `filter_prediction` and `match_score` on
explicitly constructed reference and constant completions. It also checked the
framework's built-in choice shuffle at seed 42 and preservation of correct
option text. PubMedQA uses free-form YES/NO/MAYBE accuracy; this stage does not
test every final aggregation metric. This is an offline contract audit, not
provider inference, a complete model benchmark or a report of published scores.

The native run completed successfully as GitHub Actions run `43525347543` in the
private execution repository, commit `81d137b74ff019b052f67397f2b941dde193b072`.
Its 19,921,732-byte artifact has SHA-256
`20980a25ee1f6076b30d9710f6ba5862e3825cb1fc737ba86ca5c7ff236d492c`.
`verify_capture.py` independently checks captured target semantics, row counts,
constant baselines, oracle values, question/context flags and the full SciQ join.

## Adaption status and blockers

At 23:12:31 UTC on 13 November, an authenticated read-only hosted-model catalogue
request returned HTTP 200 and listed both `gemma-4-31b-it` and `qwen3.8-27b`.
The key remained in the existing GitHub Actions secret and was not retrieved.
The check ran before third-party package installation. This stage made **zero
new model inference requests**. The previous stage made 96 real Adaption requests:
94 completed and two reached the response token limit. Catalogue availability
confirms access at the check time; it does not measure credit balance or prove
the future success of any inference request.

No operational blocker prevented this audit. GPQA authentication remains a
dataset-specific access limitation. No raw affected third-party evaluation run
has yet been established. Public usage discussion of a framework is not evidence
that a particular published score was affected.

## Research decision and next work

Keep the EvalScope result as a negative control and narrow the claim. Further
benchmark breadth alone does not close the impact gap with GAMMAF. The priority
is to obtain a version-pinned real One-Eval run with its actual prompt, response
and score artifacts, replay its native and corrected contracts, and measure
decision changes on the same fixed outputs. Until that evidence exists, describe
the confirmed findings as reproducible vulnerabilities of reference configs,
not affected published model rankings.

Develop a reusable contract checker with these healthy native corpora as negative
controls and the confirmed One-Eval cases as positive controls. Preserve every
failed hypothesis and denominator. Additional paid inference should answer a
specific unresolved consequence, rather than duplicate these deterministic
checks. No public issue, pull request or message to third parties was created.
