# Third-evaluator likelihood request contract transfer

The protocol and native source projection were frozen at private commit cd01af8f47398a96163a18da8e556937317e5066 before applying the LM Evaluation Harness methods to this selected sample. The evaluator revision is d6de81643928d653435c431bae19945d41d32520.

## What executed

The exact ConfigurableTask doc_to_text, doc_to_choice, doc_to_target and construct_requests methods, native Instance dataclass, native apply_template function, task YAML and TaskConfig defaults were executed under a documented AST dependency scaffold. Jinja2 3.1.6, MarkupSafe 3.0.3 and PyYAML 6.0.3 are pinned. No full harness dataset loader, fewshot driver, tokenizer, model, likelihood scoring or metric execution is claimed.

We selected100 ARC-Challenge and100 OpenBookQA test records by the frozen salted SHA rule from previously captured complete source splits. These official source records had already been examined in the One-Eval work. The new measurement concerns another evaluator's task and per-option request construction, not blind generalization to unseen source questions.

## Results

All200 natural cases preserved the independent source question, complete ordered choices and gold index. The native methods produced801 per-option loglikelihood request objects in the natural condition. Unlike a generation prompt, the common context need not display options: options are separate continuations. Checking only the common question string for a visible options list would impose the wrong protocol.

| Conditions | Records | Frozen v2 adapter check | Direct actual-request check |
|---|---:|---:|---:|
| Native construction | 200 | 200 PASS | 200 PASS |
| Legitimate trailing context spacing | 200 | 200 PASS | 200 PASS |
| Three controlled stale-metadata alterations | 600 | 600 PASS | 600 FAIL |

The controlled alterations remove a non-gold continuation, replace it, or remove the source question from the actual request contexts while preserving old adapter metadata. They deliberately cross v2's documented trust boundary. They are not natural LM Evaluation Harness bugs. The request-boundary check detects them by examining the actual context/continuation bundle against independent source semantics.

The final instrumented driver actually invoked a local counting function400 times for the accepted native/benign cases and zero times for the altered request bundles. No model/provider request was made. The first pass measured decisions but its backend-call field was policy-derived; that pass is preserved explicitly as INITIAL_DECISION_ONLY. INSTRUMENTATION_AMENDMENT.json records the subsequent local invocation check. Sample, methods, checker bytes and decisions were unchanged.

## Limits and research interpretation

This adds healthy source-method transfer evidence for a third evaluator, plus a concrete request-carrier check for likelihood protocols. It does not demonstrate external impact, deployment prevalence, new natural defects, full native engine integration or a universally valid checker. v2 still relies on faithful adapters. The direct boundary check is scoped to the two tasks' zero-shot likelihood construction and specified mutations.

The original v1 and experimental v2 files remain byte-pinned. New native task outcomes were not used to tune them. Natural source data are reused, and the controlled conditions repeat the same200 units; do not count1000 condition records as1000 independent questions.

## Reproduction

Extract OneEval_extensao_splits_completos_20261114.zip as BASE and OneEval_mutacoes_e_verificador_v2_20261114.zip as V2. Install requirements.txt, then run:

    python run_transfer.py BASE V2
    python verify_transfer.py BASE

The prior archive is identified by SHA-256 3c9d248d83d9c4318a121f52074a6eea8de83136da7510b0ad816d5aa36e4ae2. The v2 source hash is ced1e14f65213bc64f124a82f52f8c3a6d98b6b068026e8a0b486e8ad15228cf. Source snapshots, selected inputs, actual request captures, all exceptions/dispositions and independent verification are included. The scripts use no network or provider endpoint.

Primary source: https://github.com/EleutherAI/lm-evaluation-harness/tree/d6de81643928d653435c431bae19945d41d32520

Next: consolidate the private scientific account and claim/evidence table, including negative controls, paired model effects, adaptation false alerts, trust boundaries and exact execution scope. Further experiments should resolve a concrete remaining claim rather than repeat these diagnostic panels.

