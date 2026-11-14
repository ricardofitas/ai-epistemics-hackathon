# MixEval: task-type erasure despite schema/metadata consistency

Protocol and implementation fixed before row acquisition in commit0437942169a4b52d834b0af5b542578fc0da333e, on parent1e561b55f267aebb3be858d2cef3320723a4aa5e. One-Eval revision8aba20ad17ee2c7d2391162ac03ffaebcbb17506; upstream code hashes pinned. Official MixEval source revision66a05ec3821a2b5089ed1e32a5d65ab6ecdbf906; official custom-evaluation guide from JinjieNi/MixEval revision7c52b41929d461df7733573528bdfb08774b0c53. Prior repository name Psycoy/MixEval redirects to JinjieNi/MixEval.

The two source files each contain2000 rows. First100 per split were selected by fixed canonicalSHA256 order, without replacement:200 source units,600 condition records. These are native data-only method executions under the existing AST scaffold with a recording sink. No installed full-engine, model, tokenizer or metric-stage execution is claimed.

| Split / intervention | Source rows | Question dependence | Correct task family | MC instruction in actual request |
|---|---:|---:|---:|---:|
| Free-form / native gallery |100|0|0|100|
| Free-form / question binding only |100|100|0|100|
| Free-form / binding + typed generation repair |100|100|100|0|
| Choice / native split override |100|0|100 after label-dialect review|100|
| Choice / binding only |100|100|100 after label-dialect review|100|

The second choice condition bind_and_type equals bind_only by design; all100 outcomes were retained.

## Causal interpretation and comparison

The captured gallery selects free_form but infers key3_q_choices_a and a choice-letter parser from the existence of prompt/options/target fields. Every selected free-form row has those fields. Native preprocessing succeeds, field-presence checks pass and original route/parser metadata agree, yet all100 actual requests present the artificial option A. None and demand a choice letter. Official problem_type and target semantics identify the mismatch. Question binding alone restores the question but leaves the task-family error intact. This separates the new mismatch from the previously established symbol-binding fault.

The typed intervention changes only the free-form generation route/output instruction in addition to the fixed binding repair. It removes A. None from the delivered request and restores free-text generation in all100 cases. It deliberately does not repair the scoring/parser metadata: the original choice-letter parser becomes inconsistent with that typed route. Therefore this is a partial generation repair, not a correct complete MixEval evaluation. Free-form accepted-reference lists remain available and were never reinterpreted as positions. No accuracy, ranking change or official MixEval score is computed.

This is a concrete instance of task-kind erasure at a heterogeneous split boundary: field presence and internally consistent inferred metadata do not ensure preservation of the source task. It is not a new general theorem, a claim that schema checks are generally novel, or proof of the same defect in other evaluators. The gallery itself marks its contract inferred and smoke_passed=false; these warnings are retained and this diagnostic route is not described as a validated deployment.

## Audit errors and counterexamples retained

The frozen test expected choice rows to use problem_type=single-choice, following the official guide's example. Actual rows use multiple-choice. This produced100 source-row type alerts (300 condition appearances) in the initial captures. A separately recorded post-outcome review accepts both choice-family labels only with legal options and integer targets; all100 rows have a single legal zero-based target. These initial alerts are audit-adapter errors, not100 natural One-Eval faults. Initial captures and summary were not rewritten.

One choice row has trailing spaces in its options, which native preprocessing trims. Exact option equality passes99/100; order-preserving strip-normalized equality passes100/100. The one initial whitespace alert (three condition appearances) is retained separately. No source row, option order or scientific condition was changed after outcomes.

The variable displayed_choices in captures denotes the normalized choices available to the generator. Actual delivery is established by prompt bytes: A. None appears in all100 native/free-form and100 binding-only/free-form requests and in zero typed-repair requests.

## Scope and reproduction

The source is a benchmark mixture and can contain semantic questions already exposed in earlier project benchmarks. Metadata, documentation and one search-viewer example were visible before the protocol. No globally blind or independent-question-family generalization is claimed. This tests a new selected native configuration/split class and a predeclared structural hypothesis; post-outcome adapter review is explicitly secondary.

Run python verify_mixeval.py offline to verify the source-byte hashes, deterministic sample, references, request captures, full coverage and retained audit errors. To rerun in a copied extraction, install pandas/numpy matching RUNTIME.json and run python run_mixeval.py; this makes two pinned public downloads and overwrites results. It uses the exact upstream class bodies under the documented AST scaffold and no models. Protocol/input/native-source hashes, raw split files and captures are included. Data and source licenses are preserved with the upstream files and official README.

## External impact follow-up

Two additional pinned LoopAI report/pipeline candidates adjacent to the existing execution-log lead were inspected. One explicitly contains synthetic illustrative data; the other is conceptual pipeline guidance. Neither supplies a specifically affected original request/response and published conclusion. EXTERNAL_FOLLOWUP.json preserves paths, blobs, scope and negative disposition. Prior concrete component-execution evidence remains valid, but independent affected conclusions remain unverified. No messages, issues or submissions were sent.
