# MixEval: typed scoring, real cached outputs and denominator failure

This is new scoring work, not a rerun of the prior generation-only MixEval panel. The primary protocol was fixed before cached-response acquisition (675dcdbad4b27fe4f565a38dee365a1445d9d7ea); scoring code was committed before outcomes (e90f67c59a8e1fd4f0c9af3ddab4a9da2c10fe55). Base research/manuscript commit73ca316e6124beb4f7d0e123f9e2d125f98e48b0.

## Sources and matching

Original MixEval code and cached outputs are pinned to JinjieNi/MixEval7c52b41929d461df7733573528bdfb08774b0c53. Original One-Eval parser/metric code is pinned to8aba20ad17ee2c7d2391162ac03ffaebcbb17506. Exact Gitblob and SHA256 checks protect downloaded modules and response files.

All100free-form and100choice source records from the previous MixEval stage remain the fixed cohort. Join identity requires exact question/context, references and choice contents, with only declared null-context/type-label/target-index normalization. No unmatched or ambiguous row was substituted and the cohort was not expanded. The public response files, labelled gemma_11_7b_instruct/2024-06-01 by the official repository, contain2000rows each. Unique exact matches exist for17free-form and32choice source rows. There are128unmatched and23ambiguous source rows. This is partial coverage, not49independent new semantic question families.

## Fixed-output result

| Group | Fixed sources | Unique public-text matches | Native valid/scored references | Typed original-rule correct |
|---|---:|---:|---:|---:|
| Free-form |100|17|0/17|13/17|
| Choice control |100|32|0/32|20/32 with fixed seed42|

The same captured text is scored in both conditions. Original One-Eval choice parsing rejects every matched source reference list, including the singleton zero-based choice target lists. Both its original primary choice_accuracy function (ordinary unmodified import) and its native diagnostic rescore caller agree: they report numeric score0 while scored/valid count is0. Every per-case primary detail is None. Therefore this is not evidence of0%model accuracy, and dividing by a valid-only denominator is undefined.

The typed contract dispatches official task family, prompt constructor, accepted-reference representation, parser and score together. Complete original MixEval rule and prompt modules are imported normally, without AST extraction or monkeypatching. Free-form alias lists are preserved; choice targets are mapped from zero-based positions to source option letters. Input-generation validation uses200source prompts with official constructors; no new model answer was generated.

The typed score is the repository's optional rule-parser mode, not its default model-judge score and not a published leaderboard score. The choice rule parser falls back to a random guess in5of32matched outputs; with seed42,1of those5is correct. There are19correct non-fallback cases, so treating these guesses as unresolved gives19..24correct out of32. The primary fixed-seed result20/32is retained. The parser and reference rules differ jointly on the choice control, so its contrast must not be attributed solely to task-kind loss.

For the100-source fixed cohorts, the predeclared missing-output sensitivity is broad: free-form typed13..96correct and choice typed20..88correct; native reference-invalid scores remain unidentified on the common source denominator. No positive model-capability gain, population accuracy estimate or ranking reversal follows. The public answers came from official prompts, not faulty One-Eval prompts. The experiment isolates an assigned-score/coverage consequence on identical text and avoids the earlier omitted-question confound; it does not measure how a model responds to a changed task instruction.

## Official rule counterexamples and exploratory repair

Synthetic oracle outputs copied from source accepted aliases/choice letters pass198of200under the unmodified official rule mode. Two accepted free-form texts fail: Government of D.C. loses its terminal punctuation during parsing; Tomorrow is another day is shortened to another day by key-response extraction. RULE_COUNTEREXAMPLES.json retains exact source identities and traces. These controls are synthetic, not real model responses.

An exploratory second protocol and implementation were committed before repair evaluation (c19bbbacf0845215079af953dd03f75189188add). source_typed_contract.py adds one source-bound rule: a free-form response exactly equal to an accepted alias under edge trimming/casefold receives1, otherwise the original official-rule result is retained. It changes neither original official code nor the primary experiment. It repairs both oracle failures, yielding200/200control passes, and changes zero of the49real-output scores. This is a documented development repair, not independent validation, a new official MixEval score, or proof of general semantic-judging correctness.

## Boundaries

The explicit typed local adapter now connects route, original prompt formatting, source references, parsing and deterministic scoring. Its ordinary module path was exercised; it is not registered as an upstream One-Eval plugin, a full installed One-Eval run, tokenizer execution, provider transport or a default model-judge run. The separate diagnostic rescore caller check uses the previously documented AST scaffold; the native primary metric and official rule modules use normal complete imports.

A new matched generation trial remains scientifically useful to measure actual instruction-type behavior. It is not replaced by the synthetic controls. No current incremental provider request/token/spend allowance was established during this replay; the next executor should resolve existing authorized execution settings before launching it, rather than inventing credits or imposing a blanket model ban.

These public cached answers establish available original output text, not an external run using faulty One-Eval. No independently affected published conclusion is verified. No third-party contact, issues, PRs or publication occurred.

## Reproduction

Use a fresh Python3.12 environment and packages matching environment_freeze.txt, including CPU torch2.5.1+cpu. The dependencies are import requirements only; no model is loaded. The exact ordinary source modules are included under packages/ and selected inputs under input/.

Offline checks/replays from a copied extraction:

    python verify_scoring.py
    python check_primary_metric.py
    python check_native_caller.py
    python exact_alias_repair.py

verify_scoring.py independently reconciles source identity, coverage, source/module/cached-text hashes and original parser/score outcomes. The caller checks preserve the distinction between ordinary primary metric execution and AST method execution. exact_alias_repair.py replays the explicitly exploratory source-alias repair.

To repeat the primary public-output acquisition and scoring, python run_scoring.py downloads exactly two fixed response files and overwrites generated results. Preserve the original archive first. No credentials, tokenizer or new provider call are required. Generation prompt hashes, matched outputs, reference exclusions, random-fallback flags, oracle controls, counterexamples, original module provenance and operational failures are included. See OPERATIONAL_NOTES.json for bootstrap/verification issues corrected without modifying scientific criteria.
