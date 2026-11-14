# Unified source-bound checker entrypoint: engineering stage

`check_contract.run_source_bound_evaluation(...)` now delegates to one implementation of the trusted source -> typed request -> observed response -> structured final -> metric gate. The original normalized-contract checker and its command-line behavior are unchanged. This is a post-outcome engineering integration, not a new benchmark finding or prospective validation.

## Supported boundary

Version1 supports MixEval free-form records with explicit nonempty string aliases and string question/context, and nonstream Chat Completions under the fixed Qwen3.8-27B native source-typed profile. The legacy brace-preserving template and its system message reproduce the two archived request hashes exactly. Choice tasks, Responses API envelopes, streaming/tool/audio formats and other renderer/model profiles remain unsupported rather than silently coerced. Registering a source is a trust decision; it does not establish official-source truth.

The public entrypoint owns construction, source/reference and delivered-row checks, a single explicit transport callback, actual-wire binding, completion/model/ID checks and the optional metric callback. It copies `choices[0].message.content` literally into `provider_final_content`. It never trims that field, extracts tags, searches for aliases in the model output or substitutes an answer from the references. Original `generated_ans`, reasoning, raw response and native metric result are retained. Source, wire request, response, final content, scorer manifest and metric result hashes have distinct fields.

The registry lookup identity is separate from a source record ID. Source IDs support nonempty strings and nonnegative integers (not booleans). Delivered ID normalization is limited to exact canonical integer/string roundtrip. Unknown source/profile/ref fields fail before transport. Incomplete, malformed or unsupported captures cannot reach the metric callback. Duplicate response IDs are blocked within one run-scoped registry. A numerical zero without eligible numeric per-row evidence is UNSCORABLE; an eligible genuine zero remains a known score. The scoped single-row metric aggregate/detail and optional count fields must agree.

## Validation and what it does not show

New code is exercised against the supplied trusted native archives from runs43620987144 and43621794887. Two typed requests pass; two stock-gallery malformed requests fail before callbacks. The typed derived rows exactly equal the original installed-rescore inputs and retain all original fields. Their historical native MetricRunner results are replayed after that full-row equality check. There are ZERO new installed evaluator or provider calls in this stage. The optional adapter helper imports the real installed MetricRunner, but was not executed in this environment; full new-entrypoint installed execution remains a future boundary.

Independent test denominators are separate:

| Panel | Cases / expected outcomes |
|---|---:|
| Archived request controls (2 corrected typed,2 known stock faults) |4/4|
| Historical metric replays |4/4|
| Artificial fault inputs |106/106|
| Constructed preservation controls |7/7|
| Explicit trust-boundary demonstrations |2/2|

The independent123case suite passes after fixes. Initial114/119/123case failure reports are retained. These were bugs found while developing THIS new gateway, not newly discovered upstream benchmark faults. Separate developer regressions14/14 and original checker compatibility15/15 pass. These counts describe engineering checks on exposed data, not independent questions, prospective precision or prevalence. The source captures cover only TWO previously exposed questions; four wire requests are not four independent questions. All71extracted original files remain unchanged.

The transport callback is trusted to report bytes it actually observed and to associate a response with its request. The gate hashes supplied observations, but does not independently prove provider origin/TLS custody or semantic correctness. The independent suite deliberately demonstrates that a dishonest callback can attach a different same-model response: this is an explicit boundary, not a detection claim. A scorer callback is likewise caller-selected and identified by a declared scorer/configuration manifest.

## Reproduce offline

Run `python reproduce_entrypoint.py` after extracting this archive. It authenticates the two embedded input ZIP digests, validates ZIP paths/CRC, extracts them to real/ and rescore/, and executes original checker compatibility, new regression tests, the independent suite and the four-archive replay through the public checker entrypoint. All code, inputs and previous failed test receipts are retained. These commands make no network, generation or judge calls.

In the Git repository, the public files live beside the existing checker in experiments/contract-checker-20261114. Reports, source metadata and the offline reproduction capsule are in experiments/unified-contract-entrypoint-20261114. The required captured regression inputs are embedded in this durable capsule; tests that consume those archives are not self-contained without extraction. Caller code can import SourceRegistry/TransportCapture from source_contract_gateway and run_source_bound_evaluation from check_contract; replay_existing.py is a complete zero-call example.

## Independent comparator gate: negative capability result

A source-only official EvalScope inspection pins commit59bb367bd8565f347266a48ac1230af0b5131b97. Its registered ExactMatch.apply unconditionally lowercases both values through normalize_text, whereas the prepared protocol deliberately requires case-sensitive trimmed equality. No normalizer-disable parameter is present in that registered callable. The protocol therefore stops UNSUPPORTED_COMPARATOR before any replay, rather than switching to an unregistered utility or changing the contract to manufacture agreement. This is NOT an EvalScope scoring bug or independent validation of our gateway. Source files, exact blob/SHA256 pins, unchanged draft and explicit metadata-acquisition amendment remain in the capsule. No new question or response acquisition occurred for this comparison.

## Continuity and next action

The canonical manuscript remainsv1.7/PDF-sourceZIPversion7 with20claims. This stage does not add a scientific claim or change prior scores. Preserve the independent authorized3200slot Adaption campaign owned by the direct research thread; do not launch a parallel batch or reinterpret its budget. Its source families, model catalogue, caps and wave results must be checked from that campaign's own saved protocol/checkpoint. Next useful integration work is an isolated installed execution of this new entrypoint or explicitly versioned support for additional task/provider/model profiles using authenticated captures, not repeating completed model batches. Independent consumer comparison requires a new declared compatible contract before any scoring.
