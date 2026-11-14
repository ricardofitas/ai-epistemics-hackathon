# WinoGrande: reference-only consequence replay

This follow-up reuses the existing 13 November model experiment. It makes no new provider or judge calls and does not alter the manuscript or review workbook.

## Result

On the same 12 balanced labelled validation questions and the same 24 archived model outputs:

| System | Original metric | Source-canonical reference, same original parser |
|---|---:|---:|
| Gemma-4-31B-IT | 50% | 11/12 known correct, one unknown: 91.67–100% |
| Qwen3.8-27B | 50% | 12/12 = 100% |
| Constant B | 100% | 6/12 = 50% |

The model-versus-constant comparison reverses even under the worst possible label for the one incomplete response. The actual native scorer returns 11/12 for Gemma after correction; the 11/12–12/12 interval separately retains uncertainty about the incomplete response.

The native parser and full evaluation contract are unchanged in all WinoGrande metric invocations. Their parser configuration SHA256 is `a3420f98f12da3da15239b03ec43b4dbbaa013d198a59be5f85cd09d6a16afb6`. The result is reproduced by two interventions:

1. Keep every source row, original reference and raw prediction unchanged; select an added source-canonical reference column using `ref_key`.
2. Keep the original `ref_key`; change only the original `answer` field from its source numeral to the corresponding canonical answer tag.

Both repairs agree. Prediction parse results remain identical. The original reference labels `1` and `2` both normalize to `B`; the repaired references normalize to A or B according to the one-based source semantics.

The full 1,267-row labelled validation source is also replayed with explicitly constructed controls:

| Constructed predictor | Original metric | Reference-only correction |
|---|---:|---:|
| Perfect source oracle | 639/1267 = 50.4341% | 100% |
| Constant B | 100% | 639/1267 = 50.4341% |

These 1,267-row predictions are controls, not additional model responses. On the healthy HellaSwag control, original and reference-only metrics both retain 11/12 for each model.

## Precise consequence

The published metric implementation can prefer a constant answer to a model whose returned choices are nearly perfect on a valid labelled source panel. Correcting only the encoding of source gold reverses that comparison, without changing the returned model answers. This closes a local causal consequence at the comparison level, not just an input-format diagnostic.

The comparison does not establish that an independently published leaderboard was affected. The selected WinoGrande split is validation; the gallery's default test split has no public labels. The stored model prompts were intended gallery prompts rendered from source fields, not the defective full native generator route. The gallery marks the contract `reference_mapped`, `smoke_passed=false`; this is a reproducible labelled diagnostic configuration, not evidence of validated deployment. No statement of novel general mechanism or superiority to GAMMAF follows automatically.

## Reproduction

`replay.py` uses original registered metric, parser, MetricRunner and BenchInfo through ordinary imports. Only the original preprocessing class is isolated by its unchanged AST body, to avoid unrelated provider dependencies. No graph, generation or HTTP stage is invoked.

Required pinned inputs:

| GitHub Actions repository | Artifact ID | SHA256 |
|---|---:|---|
| ricardofitas/swarm-adaption-hackathon | 14081991998 (model capture) | 2a9abd3fd0c5f9108dd4c3812fba5d64c168b6e414d34e3b41191df869ba13df |
| ricardofitas/swarm-adaption-hackathon | 14080941663 (source capture) | a43b28ce6c9219c7c2155d979b2df2a54645e636f1ef1384256522c238a90a39 |
| ricardofitas/swarm-adaption-hackathon | 14082591487 (locked code support) | 945d064d442df8166bd4731ed03d478cb354c525792bf8c8441f922c61256dd8 |

The two capture ZIPs are read directly and authenticated before processing. `cases.json` and `manifest.jsonl` also match the protocol's frozen SHA256 values. All 24 WinoGrande source rows, request hashes and raw output hashes are verified against those captures. Original native source files are authenticated with the Git blob identities and SHA256 values retained in the support package's `UPSTREAM_SOURCES.json`.

Use Python 3.11 with pandas, numpy and the original One-Eval source dependencies installed. Extract the locked support and supply its `oneeval_alias_evidence_20261113` folder. Its original `one_eval/logger.py` is required for ordinary imports; obtain it from One-Eval commit `8aba20ad17ee2c7d2391162ac03ffaebcbb17506` if absent from that old support archive. Use the original `default_contract_audit_20261113/upstream/dataflow_eval_tool.py` as the preprocessor source.

```bash
python replay.py --support-dir PATH/oneeval_alias_evidence_20261113 --preprocessor PATH/default_contract_audit_20261113/upstream/dataflow_eval_tool.py --model-archive model-capture.zip --source-archive source-capture.zip
```

Outputs are `proof/RESULT.json`, `proof/MODEL_SOURCE_IDENTITY.json` and `proof/WITNESSES.json`. `RESULT.json` contains native module origins, authenticated source identities, all metric results and scope boundaries. The root agent separately verified the 24 raw source/request/output associations and model correctness counts; this replay independently executes the original native scoring route.
