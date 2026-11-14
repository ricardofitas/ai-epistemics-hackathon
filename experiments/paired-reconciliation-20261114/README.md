# Paired trial reconciliation and score factorization

This post-hoc reanalysis reconciles the already executed 200-request WinoGrande trial. Existing aggregate results were inspected before the specification was frozen at df71ce6a4b97627e1c44f108463177a8aeccb736. No new inference was performed and none of the source trial responses was replaced.

## Fixed-output scoring and prompt conditions

The same pinned native heuristic parser is used for both reference routes.

| Model | Native prompt, shipped references | Native prompt, source references | Corrected prompt, shipped references | Corrected prompt, source references |
|---|---:|---:|---:|---:|
| gemma-4-31b-it | 6% | 18% | 46% | 88% |
| qwen3.8-27b | 0% | 46% | 48% | 88% |

Changing only references on corrected-prompt outputs changes assigned scores by +42 pp and +40 pp respectively. The constant-B scorer diagnostic changes from 100% to 50%, as documented in the original paired trial. These are finite fixed-output scoring consequences. They do not measure an improvement in model capability.

The prompt/reference interaction is +30 pp for Gemma and -6 pp for Qwen. Thus the reference effect depends on the output set, and a single prompt effect plus a single reference effect should not be generalized across paths. Both exact algebraic decompositions of the joint assigned-score change were verified. This is a descriptive accounting of the captured outputs, not an independently identified mechanism or a new randomized experiment.

## Strict answer evidence and unknowns

The original strict primary rule requires a completed response with exactly one legal answer tag. For Gemma, native prompts have 3 known-correct and 46 unknown out of 50; corrected prompts have 44 known-correct and zero unknown. The unknown-as-zero gain is +82 pp, but worst/best sensitivity spans -10 to +82 pp. It does not establish a robust positive accuracy gain under that unknown policy.

For Qwen, native prompts have 23 known-correct and three unknown out of 50, versus 44 known-correct and three unknown under corrected prompts. The observed gain is +42 pp; sensitivity remains +36 to +48 pp.

The source label is independently recovered from each captured original record, its source hash is checked, and all native parser cells are checked against the original published analysis. There are 50 selected questions in 35 dependency groups, reused across two models and two prompt conditions. The diagnostic selection is enriched for input collisions and does not estimate deployment prevalence. Repair changes question binding and unresolved brace formatting jointly; the design does not isolate those two changes.

## Capture and resource reconciliation

The independent existing request/SSE verifier was rerun successfully: 200 unique requests, one attempt each, HTTP200 throughout, 194 completed responses and six incomplete responses; request bodies, terminal responses, stream and artifact hashes match.

Usage was summed once per request, including incomplete responses: 14,547 input tokens, 97,047 output tokens, 111,594 total tokens. The provider cost fields sum to approximately 0.109769073 reported units. Currency, actual billed amounts, earlier project-wide consumption and remaining credits remain unverified; this number is not presented as USD.

The execution provenance issue is resolved. Runs43533000838 (paired model trial, head93f8ca4dc2fc7f7826dfbc82d6a36698419f0a00) and43541759934 (four-contract audit, headad8249103b369e6bac5de9eb43590c3cc3615838) currently resolve as completed/success in ricardofitas/swarm-adaption-hackathon. The research source and results are maintained separately in ricardofitas/ai-epistemics-hackathon. The earlier404 arose from querying the execution run under the research repository.

External independently used affected scores remain unverified.

## Reproduction

The input archive is included unchanged under input/. Extract it as BASE, then run:

    python BASE/oneeval_paired_20261114/verify_capture.py
    python reconcile_trial.py BASE

The capture verifier uses the standard library. Reconciliation uses pandas plus the pinned native source scaffold included in the original archive. No network or model endpoint is called. Original input hashes, specification, recomputed per-request outcomes and resource breakdown are included.

Next: preregister genuinely new validation for the experimental source-bound checker in an additional evaluator, including legitimate formatting changes and prompt/metadata consistency; retain all existing development and negative evidence.

