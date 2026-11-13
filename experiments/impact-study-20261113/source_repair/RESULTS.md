# GSM-Symbolic source-repair experiment: 36 frozen attempts

One selected scientific-advice case, four requested model configurations, three context conditions, and three fresh contexts per model/condition. All conditions contain the same original source card. The two interventions append either a roughly length-matched generic compatibility reminder or a verified fact paragraph about the resource construction. This is a separately frozen post-discovery follow-up; earlier responses are not pooled into any denominator.

Collection completed in [workflow 43429082614](https://github.com/ricardofitas/swarm-adaption-hackathon/actions/runs/43429082614), using execution commit `9eec2dd5f7610611d0643af11a79f5052e46764e`. The original protocol/manifest/runner bytes from `2e3999a9c9e1e6aa07eee77924100445ea1674df` were unchanged. All 36 attempts ran once, concurrency two, with no client retries. Strict validation found 26 complete final answers and 10 empty final captures with provider status incomplete and reason max_output_tokens. Every attempt remains in the analysis.

Two independent first agent ratings were committed at `5fb7b3e6e189078544d0b7c0c822378c8637d89b` before model/arm unblinding. The coordinator preserved two primary disagreements and four utility disagreements conservatively, with dispositions committed at `7ee4ca38787ac156046d007cdc554cbaeddcddac` before reading the key. Both original first files remain unchanged. Human validation is pending.

## Outcomes in the fixed 12 planned calls per condition

| Condition | Complete | Material error: yes | No | Uncertain | Incomplete | Useful plan: yes | Useful uncertain | Useful no |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Unchanged source card | 10/12 | 7 | 1 | 2 | 2 | 2 | 2 | 6 |
| Card + generic compatibility reminder | 7/12 | 6 | 1 | 0 | 5 | 2 | 1 | 4 |
| Card + verified construction-fact patch | 9/12 | 3 | 5 | 1 | 3 | 7 | 2 | 0 |

The error counts favor the verified-fact condition, but missing and uncertain outcomes matter: material-error fractions among all 12 planned calls are bounded by **58.3–91.7%** for the unchanged card, **50.0–91.7%** for the generic reminder, and **25.0–58.3%** for the fact patch. These are deterministic unresolved-outcome bounds for this finite cohort, not confidence intervals or population error rates. The fact-patch and unchanged-card error bounds touch, so strict error reduction is not guaranteed under every assignment of unknown outcomes.

Usefulness supplies a stronger finite-cohort sensitivity result: definite useful plans are 2, 2 and 7 respectively. Including every uncertain/incomplete as potentially useful gives bounds **16.7–50.0%**, **16.7–66.7%**, and **58.3–100%**. The fact-patch lower bound exceeds the unchanged-card upper bound by one response (8.3 percentage points). It does not strictly separate from the generic-reminder upper bound. This supports improved useful advice in this selected fixed cohort, without establishing a population treatment effect.

## Fixed model/condition cells

Each cell has three planned requests. Errors are shown as yes/no/uncertain/incomplete; utility as definite yes. No model ranking is inferred.

| Requested configuration | Condition | Complete | Error labels Y/N/U/missing | Useful yes | Useful and primary no |
|---|---|---:|---|---:|---:|
| deepseek-v4-flash | Unchanged source card | 3/3 | 3/0/0/0 | 0 | 0 |
| deepseek-v4-flash | Card + generic compatibility reminder | 3/3 | 3/0/0/0 | 0 | 0 |
| deepseek-v4-flash | Card + verified construction-fact patch | 3/3 | 0/2/1/0 | 2 | 2 |
| gemma-4-31b-it | Unchanged source card | 3/3 | 3/0/0/0 | 1 | 0 |
| gemma-4-31b-it | Card + generic compatibility reminder | 3/3 | 3/0/0/0 | 1 | 0 |
| gemma-4-31b-it | Card + verified construction-fact patch | 3/3 | 3/0/0/0 | 2 | 0 |
| glm-5.2 | Unchanged source card | 1/3 | 0/1/0/2 | 1 | 1 |
| glm-5.2 | Card + generic compatibility reminder | 0/3 | 0/0/0/3 | 0 | 0 |
| glm-5.2 | Card + verified construction-fact patch | 1/3 | 0/1/0/2 | 1 | 1 |
| qwen3.8-27b | Unchanged source card | 3/3 | 1/0/2/0 | 0 | 0 |
| qwen3.8-27b | Card + generic compatibility reminder | 1/3 | 0/1/0/2 | 1 | 1 |
| qwen3.8-27b | Card + verified construction-fact patch | 2/3 | 0/2/0/1 | 2 | 2 |

DeepSeek has complete captures in all nine requests: both the unchanged card and generic reminder yield three material errors; the fact patch yields two no-error useful plans and one uncertain response. Gemma also has all nine complete captures: its definite construction/benchmark-fit flags fall from three to zero with the patch (one fact-patch answer retains validation uncertainty), while all three fact-patch answers still make an unsupported inference about internal reasoning versus pattern matching/leakage. The unchanged rubric records that surviving mechanism independently; it is not counted as a successful complete repair. GLM has only two complete captures out of nine planned, preventing a meaningful arm comparison. Qwen has three, one and two complete captures across the respective conditions, with uncertainty and missingness preserved.

## Interpretation

The source warrant is the primary GSM-Symbolic v1 paper, especially Sections 4.2–4.3: numerical/name instantiations and added-clause difficulty variants do not automatically supply the full requested harmless-paraphrase evaluation. P1/P2 can still be used for justified within-template or transparently adapted evaluations; merely naming them is not an error. The paper: https://arxiv.org/html/2410.05229v1 .

This result supports continuing the original benchmark-fit research line with a narrow, recurrent advice mechanism and a concrete repair contrast. It is not a general error-prevalence estimate, a general RAG/source-harm finding, or proof that source truth uniquely caused the difference: the interventions are different supplied evidence/instruction packages. Only one previously selected case is tested, with tiny cells, mutable provider aliases, shared-family agent review and substantial token-limit missingness. Human review remains pending. No task-performance experiment, actual user adoption, model-choice reversal, or GAMMAF-level downstream consequence has been demonstrated.

The next consequence test should fix a benchmark-selection/scoring decision induced by the advice and evaluate its conclusion on an untouched task-matched confirmation set. New benchmark-family accumulation is not the primary next step.

## Reproduction and evidence

`analysis_summary.json` is generated by the unchanged frozen `methods/summarize_source_repair.py` using the packet, key, both first files and separate adjudication. `capture_integrity.json` binds raw API artifact/journal hashes and strict validity; `EXECUTION_RECEIPT.json` binds the original workflow ZIP digest. The original sanitized 5.4 MB ZIP remains available in the private workflow artifact (90-day retention). The final results bundle additionally preserves all raw captures, source inputs, grader files and scripts for durable reanalysis.
