# SQuAD: captured final-answer consequence confirmed by the public official scorer

Status: **controlled causal-panel consequence verified; ordinary One-Eval SQuAD attribution remains unestablished**. This is a retrospective independent implementation check of existing captures, not a new model experiment.

## What was verified

The original prospective study fixed 100 SQuAD questions, four models and four prompt conditions before generation. The question, source passage, temperature and per-question output cap were kept fixed. The present audit authenticated all eight original capture ZIPs from run `43624040280`, the original SQuAD development source, and the frozen cases/design/scoring files. It checks **1,539 complete and 61 unknown responses out of 1,600 planned SQuAD requests**. Requests are repeated observations of 100 source questions, not 1,600 independent problems.

The unchanged public SQuAD scorer maintained in `huggingface/evaluate/metrics/squad/compute_score.py`, Git blob `e60acfd1044319e43a59ffe8db75e63b68785ba7`, was imported and its complete `compute_score` function executed on the selected original SQuAD records. Predictions use the primary study's prespecified last-answer-tag extraction (last nonempty line fallback). Every completed exact-match label agrees with the original endpoint. This closes an independent public metric check for this controlled cohort; it does not establish a new scorer defect.

## Actual observed consequence

| Model | Correct without dummy, wrong with dummy | Of those, literal A/None final | Unknown pairs | EM drop bounds |
|---|---:|---:|---:|---:|
| Gemma-4-31B-IT | 81 | 81 | 3 | 80–84 pp |
| Qwen3.8-27B | 50 | 50 | 12 | 44–56 pp |
| DeepSeek-V4-Flash | 44 | 42 | 17 | 40–57 pp |
| GLM-5.2 | 41 | 41 | 19 | 36–55 pp |

The compared pair holds the choice instruction fixed and changes only insertion of `Options:\nA. None`. Across models there are 216 correct-to-wrong completed pairs, of which 214 end with literal A/None. There are four opposite-direction completed pairs. The equal-weight mean drop remains **50–63 percentage points** when all unknown outcomes receive their best/worst scores. These are fixed-panel sensitivity bounds, not confidence intervals or a benchmark-wide prevalence estimate.

The primary design deliberately includes a mismatched contract: `choice_clear` requests selection from provided options while listing none; `choice_none` lists the sole non-factual placeholder. Therefore these conditions must not be presented as two equivalent, valid multiple-choice tasks. The consequence is that changing this contract can replace an available factual answer with a placeholder. It is not evidence that adding a harmless string reduces the model's knowledge.

## A source-authenticated witness across all four models

SQuAD ID `5711541350c2381900b54a70`, topic `Steam_engine`:

> What nationality was Arthur Woolf?

The preserved source passage explicitly calls him a British engineer. Its accepted answer is `British`. All four models return **British** under `choice_clear` and under `free_none` (which retains the same dummy option while requesting a factual free response). All four instead return **A** or **A. None** under `choice_none`.

For each of the four models, the comparison's actual serialized payload hashes were checked against the frozen design and attempt records. Terminal SHA256, returned model, response ID, final output bytes, source record hash, question, passage and gold spans were verified. The choice-pair payloads differ only by that exact option insertion. `WITNESS.json` retains the source, final answers and request/response hashes. The witness was selected deterministically by maximum model coverage and then source-ID hash; 82 source questions have at least one completed model witness meeting the clear-correct, free-none-correct, choice-none-dummy pattern.

## Closure decision

| Boundary | Result |
|---|---|
| Original source and selected questions | PASS |
| Actual serialized experimental requests | PASS |
| Authentic captured final outputs | PASS |
| Complete public SQuAD scorer execution | PASS |
| Minimal controlled change and free-response control | PASS |
| Supported ordinary One-Eval SQuAD generation | NOT EXECUTED |
| Attribution to a naturally occurring native SQuAD pipeline fault | UNESTABLISHED |
| Changed external published conclusion | UNESTABLISHED |

The option manipulation was deliberately introduced by the prospective experiment. These traces use Adaption's Responses API, not the native One-Eval ChatCompletions pipeline. The older native four-request archive was authenticated separately, but its source questions concern Dance and Tony Blair rather than SQuAD, and its native exact-match endpoint was an explicitly selected integration diagnostic. Those two cohorts cannot be combined into an unbroken native SQuAD execution claim.

This provides a concrete, reproducible consequence in a controlled SQuAD panel: the apparent factual failure can be caused by task/answer-contract substitution, despite the same model supplying the fact under the control. It corroborates the existing panel effect with a separate official-scorer implementation and a four-model witness. It does not establish a benchmark ranking reversal, a new natural fault prevalence, or superiority over GAMMAF.

An independent assistant checked all nine archive digests and 3,311 extracted members byte-for-byte, source spans, all 1,600 SQuAD slots, every final EM/F1 label and the paired counts. Its verification passed and agrees with the scope limitation: this is task-contract perturbation, not an information-equivalent format-only change, and the SQuAD scorer itself is not shown to be wrong. This is independent assistant verification, not independent human review or new model evidence.

No new model/judge calls were made. No manuscript or human workbook was modified. No annotations are described as independent human judgments.

## Evidence and reproduction

- `ACQUISITION.json`: exact original artifact digests and sizes; no signed URLs.
- `SOURCE_PINS.json`: exact Git blobs of cases, design, scoring and official scorer.
- `RESULT.json`: all per-model official exact-match/F1 intervals and closure limits.
- `OFFICIAL_SCORE_LEDGER.jsonl`: all 1,600 SQuAD slots, final-answer views and trace identities.
- `WITNESS.json`: the four-model source example and retained hashes.
- `analyze_consequence.py`: verification and full public-scorer replay; see `README.md`.
- `INDEPENDENT_AGENT_VERIFICATION.json` and `independent_agent_verify.py`: separate assistant audit of source/capture bytes and arithmetic.
