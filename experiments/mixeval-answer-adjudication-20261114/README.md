# MixEval: final answers, non-final information and rule credit

A post-generation, reference-grounded output audit of the already completed80request pilot. No generation was resumed or retried; no new provider or judge API calls were made. Two assistant agents independently annotated69complete responses under a fixed rubric committed before adjudication (eee9572f4a45bd9479ccbe6dd7d9cd0c516454c5). Eleven incomplete captures remain unknown. This is a new interpretation audit on existing responses, not a new source cohort or an independent human/default-judge evaluation.

## What changed scientifically

The original rule scores remain unchanged. Evaluating the final answer and looking for supported content elsewhere in the output answers different questions:

| Model/condition | Complete / fixed20 | Original rule correct | Supported final answer | Supported non-final content |
|---|---:|---:|---:|---:|
| Gemma binding-only |18|11|2|17|
| Gemma typed |16|12|12|1|
| Qwen binding-only |18|2|2|2|
| Qwen typed |17|14|15|1|

Both reviewers identify16symbolic final answers among18complete binding-only responses for each model. For Gemma,9rule-credited responses have a symbolic final answer;15responses state accepted information outside that symbolic final answer. These categories overlap and do not add independent questions. In this panel, the rule evaluator may credit material outside the final answer, so its Gemma contrast cannot be read as a direct measure of final-answer improvement. Visible content is not hidden reasoning or evidence of internal knowledge.

Under the frozen alternative final-answer rubric, typed-minus-binding bounds across the same20source questions are Gemma+40..70pp and Qwen+55..80pp. The original optional-rule bounds remain Gemma-5..25pp and Qwen+50..75pp. These are missing-capture/adjudication bounds, not confidence intervals or population/model-capability gains. They do not retrospectively replace the original experiment's endpoint.

One Qwen typed response is labelled final-supported by both reviewers while the original rule gives zero: “Prepare for the worst.” versus accepted “But prepare for the worst”. The reviewers judge the omitted conjunction immaterial in the proverb-completion question. This is a stated semantic-equivalence judgment, not an exact-alias match or independent factual truth validation.

## Procedure and limits

Models, conditions, paired identities, requests and individual rule scores were hidden behind opaque SHA256identifiers and a fixed order. The agents read only the frozen protocol and blinded cases. The protocol disclosed aggregate earlier observations, and response style can reveal the condition, so blinding is partial. Both reviewer label sets agree69/69forfinal and69/69fornonfinal. Reviewers share a model family/rubric; agreement does not establish independent errors or human validation. Official aliases serve as trusted reference proxies; they were not independently fact-checked.

SUPPORTED final requires an affirmative accepted answer/minimal semantic equivalent in the final span. An isolated A is SYMBOLIC even when earlier visible text contains the accepted fact. Non-final support requires an affirmative reference-supported statement outside that span, not a hypothetical or negated mention. The protocol fixes conservative disagreement handling; no adjudicative consensus rewrite was needed. All labels and exact evidence spans remain available.

The third agent independently checks all source/request/text hashes,69unique label IDs per reviewer, exact quote placement, original69rule scores and all80records/paired arithmetic. Free-form parser output uses list(set(...)); the verifier explicitly compares only that order-insensitive field as a multiset. Scores and every other judged field remain exact. This verifies integrity/arithmetic, not semantic truth.

The20source questions are previously exposed (16TriviaQA/3DROP/1BBH) and repeated across two models; they are not40independentquestions. Instructions/format change jointly and request order is fixed. No new independently affected external conclusion was found or claimed. The earlier minimal-local-error analyzer issue did not occur in the80actual receipts, remains a future-hardening task, and was not reannounced as a failure of this experiment.

## Reproduction

Extract this package preserving directories, then extract `inputs/Epistemics_MixEval_integracao_e_geracao_emparelhada_20261114.zip` into `package/`. Run `python work/build_blind.py`, `python work/aggregate.py`, then `python work/verify_adjudication.py`. Reviewer judgments are retained data, not automatically regenerable gold labels; the verifier checks their quoted evidence and aggregation. `package/real-generation` contains immutable original study inputs, outputs and scorer implementation; no command launches generation. The separately updated canonical manuscript sourceZIP provides `verify_claims.py` for manuscriptv1.5and16claims and `render_manuscript.py` for14pages with8mainpages. Font/runtime requirements are retained from the source package.

## Next evidence needed

Independent human or separately authorized semantic judging should test the reference-equivalence judgments and final-span convention. A new informative prospective cohort/minimal intervention must separate task-kind wording from other format changes; no further batch is authorized by this output audit. Future integration should repair source/scorer provenance labels and local-error classification under a new receipt, without rewriting frozen results. Existing external-impact leads remain bounded.
