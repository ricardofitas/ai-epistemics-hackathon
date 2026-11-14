# Independent retained-evidence review: natural CUPCase consequence

## Verdict

**A concrete scoped causal measurement consequence is established.** In the pinned One-Eval source-loaded evaluation entry point, a serving program that always emits `<answer>A</answer>` obtains a selected report score of 100% on all 3,562 CUPCase records even though no captured request includes its own clinical case. Original gallery mapping places `correct_diagnosis` first, and the source placeholder remains unresolved in every request. A source-preserving correction restores the case and neutralizes option ordering; the identical constant output then yields 905/3562 = 25.407074677%. Every corrected A score flag, not only the aggregate, equals the source correctness of the displayed first option. This is not an inference about clinical reasoning: the predictor ignores every input.

The corresponding all-A MMLU control receives 3222/14042 = 22.945449366%, with every question present. The source cases and labels are not deliberately corrupted to manufacture the original effect.

## Independently checked

- Original source-loaded entrypoint artifact 14132959007, run 43645404107, SHA256 `0fff22307ea63ae0bbe15a9e03088344ce9479cf5d64d4d196e03efa2ed9871b`.
- Corrected-entrypoint artifact 14133559844, run 43645998862, SHA256 `66de2030edca15d53c8318b59821d2e8ef06c31f3e94f8e7cba6d2bd4b5378fe`.
- Recounted original source positions, selected report scores, native valid/score flags, every prompt hash and question-presence flag, per-result SHA256s and exact source task fields.
- All original five CUPCase fields identical before and after repair, checked from preserved `source-before-native.jsonl`; source JSONL itself is augmented by native preprocessing and must not be confused with the pre-native source snapshot.
- Corrected neutral choice lists reproduce the prespecified Python random seed and preserve each original four-option multiset.
- Corrected A confusion: 905 true positives, 2657 true negatives, zero discrepancies.
- Corrected B confusion: 882 source-correct rows, six additional false credits; native score 888/3562. Retain this residual parser discrepancy. Do not describe the complete parser as repaired or report B=882 as the observed native score.
- No additional native pipeline run or model/judge call was made by this reviewer. These are independent arithmetic and retained-artifact checks of the owner's experiments.

## Propagation and metric distinction

`ReportGenAgent._resolve_report_score` at One-Eval `8aba20ad17ee2c7d2391162ac03ffaebcbb17506` selects `bench.meta.eval_result.accuracy/score` without checking the diagnostic role. The stored selected diagnostics are explicitly `role=diagnostic`, `display_as_primary=false`, while the gallery declares `score_source=metric_stage`. The function returns 1.0 for original CUPCase constant A. Removing only the diagnostic metadata returns `dataflow_eval:missing` and 0.0; it does **not** fall back to the declared primary metric.

The ordinary metric stage also displays 0.0 on every tested source; its stored `pred_choices` are all None. This is not a valid zero-capability result or a semantic correction. Keep these score paths distinct.

## Other original splits

The same immutable-source path yields all-A selected scores 994/997 valid SciQ rows (1000 source; three invalid references), and 412/427 valid GPQA rows (448 source; 21 invalid references). All 448 GPQA prompts omit their own question. Preserve these denominators. GPQA question content was not printed or included in this review.

## Scope limits

The experiment executes complete original `DataFlowEvalTool.run_eval`, real disk storage, original generator/evaluator/rescorer, native MetricRunner and report score-selection functions in a source-loaded dependency boundary. It uses a constant serving cache, AST-loaded classes and declared inert/non-evaluation dependencies. It is **not** a fully installed ordinary CLI run, LLM-produced final report, historical released benchmark score reproduction or a demonstrated reversal of a published clinical-model ranking.

CUPCase gallery readiness is `contract_inferred`, `smoke_passed=false`; SciQ/GPQA/MMLU are reference-mapped but also not smoke-verified. Therefore describe this as a concrete failure of the shipped gallery/source-loaded evaluation path, not an audited official CUPCase author's evaluator or unrestricted supported-use claim.

The repair jointly restores question binding and fixes the displayed/reference order. A constant response can isolate the position-leak effect but cannot estimate the capability gain from restored question text. The source-linked 100%→25.407% selected-score consequence is strong without asserting either novelty or superiority to GAMMAF.

## Local reproducibility

`verify_retained_entrypoint.py` reconstructs original counts from authenticated artifact bytes; `verify_repair.py` checks the repair and residual B discrepancy. Outputs are `INDEPENDENT_ENTRYPOINT_RECOUNT.json` and `INDEPENDENT_REPAIR_RECOUNT.json`. The artifacts remain under `archive/` and `repair_archive/`.

Relevant research protocol commit: `c3003a6ae3fc1c6367a3199c24030cc4ef40328a`; corrected parser/display alignment research commit: `bc942e1b390784d76b85507c78203b32315c0c8b`. No branch was modified by this reviewer.
