# Installed native source/request gate integration

Protocol and code were committed before outcomes:36524a3e08213af5236139a13a6b05c4c48b5a7a, based on research7f44f5986711fecf1d0bf18342cd6c6a82e4b42d. This is a separate experimental native-request gate; the original checker and source-boundv2 were not modified.

Unmodified installed lm_eval0.4.14.dev0, revisiond6de81643928d653435c431bae19945d41d32520, loads local frozen records with ConfigurableTask and builds real native Instance objects. Six installed native module hashes and all seven recorded principal dependency versions match persistent prior provenance. No AST projection or source monkeypatch is used.

A trusted registry is built directly from the previously captured official-source records, independent of runtime Instance metadata. The gate checks the source document digest, document/option identifiers, question in actual contexts, exact official option continuations and native target. It serializes an immutable primitive snapshot and sends that same verified snapshot to a local counting function only after PASS. This explicitly ends at a counting sink, not an LLM backend.

| Condition | Reused source units | Gate outcome | Counting calls |
|---|---:|---|---:|
| Healthy native requests |200|200 PASS|200|
| Benign actual-context spacing |200|200 PASS|200|
| Drop non-gold continuation |200|200 FAIL|0|
| Replace non-gold continuation |200|200 FAIL|0|
| Remove actual question |200|200 FAIL|0|
| Wrong native reference |200|200 FAIL|0|
| Substitute Instance document |200|200 FAIL|0|
| Missing trusted source registry key |200|200 INCOMPLETE|0|

There are200 reused source units (100ARC-Challenge and100OpenBookQA),801 native option objects and1600 conditional variants. All400 approved snapshots reached the counting sink byte-identically under canonical serialization, representing1602 option requests across those two accepted conditions. No failed or incomplete case reached the sink. Independent offline source/capture/denominator/dispatch reconciliation passed. ERRORS.json is empty. Zero model/provider calls or model instantiations occurred.

These are deliberate known-mechanism controls on reused records; no new natural engine defect, source-independent generalization, deployment prevalence or model accuracy is claimed. The trusted source archive remains an explicit assumption. No tokenization, model execution, remote provider transport, score computation or arbitrary adversarial software was tested.

## Reproduction

For offline result verification, only standard-library Python3 is needed:

    python verify_native_gate.py

For native execution, create an isolated environment, install the exact public EleutherAI/lm-evaluation-harness revision above and match environment_freeze.txt. Principal dependencies and six native module hashes are required by the executable checks. The original runtime reused a verified installed package cache; the new code and inputs come entirely from this persistent package and do not require prior temporary files.

Use a copied extraction because generated outputs are overwritten:

    python run_native_gate.py
    python verify_native_gate.py

The native run sets Hugging Face offline flags. All200 trusted source records, resolved native configs and prior dependency/source provenance are under input/. The public installed package is an explicit external dependency, not included in this archive. The dataset cache and virtual environment are excluded. No credentials or model access are needed. Python runtime version is captured in RUNTIME.json.
