# ARC/OpenBookQA: crédito para letras que o pedido não oferece

14 November 2026. Bounded component verification, no model or judge calls.

## Concrete consequence

Using 100 previously frozen questions from each of ARC-Challenge, OpenBookQA and the healthy MMLU control, the installed unmodified DataFlow generator forwards the same original prompts captured in the earlier audit. In ARC/OpenBookQA the displayed answer set has two aggregate entries, A and B. The original OneEval metric still accepts letters A–D.

| Cohort | Source questions | Question present | Full source choices preserved | Source-letter replies not offered | Replies nevertheless credited |
|---|---:|---:|---:|---:|---:|
| ARC-Challenge original | 100 | 100 | 0 | 46 | 45 |
| OpenBookQA original | 100 | 0 | 0 | 43 | 43 |
| MMLU healthy control | 100 | 100 | 100 | 0 | 0 |
| Each cohort after choices + question binding repair | 100 | 100 | 100 | 0 | 0 |

The response fixtures return the source's canonical gold letter. They are constructed scoring diagnostics, not model answers and not feasible oracles for the malformed two-choice tasks.

Original source-letter fixture accuracy is 98/100 for ARC, 100/100 for OpenBookQA and 100/100 for MMLU. These numeric scores stay identical after the input repair. This is the important consequence: a high scalar score can conceal both an absent question and credited letters that were not individually offered as options. The 2 ARC reference-mapping errors remain present; no source-reference correction is folded into the input intervention.

A constant C fixture receives 24/100 in ARC and 26/100 in OpenBookQA, although C is never an individually offered option in these original model-facing prompts. The healthy MMLU constant-C fixture receives 28/100 with C legitimately present.

## Causal isolation

Four conditions were run with identical source records, original references, response bytes, original metric and parser:

1. Original archived preprocessing and original template.
2. Choice decoding only.
3. Question binding only.
4. Both input repairs.

Choice decoding alone restores complete choices in ARC and OpenBookQA. In OpenBookQA, question binding alone restores the question but leaves the aggregate options. Both are required for a fully source-bound task. All conditions preserve the healthy MMLU control. No purported change in model capacity or published ranking is inferred.

## What executed

- CPython 3.11.18; installed open-dataflow==1.0.10.
- Ordinary imports of unmodified BenchAnswerGenerator, FormatStrPrompt and disk-backed FileStorage; decorators and native file reads/writes remained active. The three source files exactly match the downloaded wheel.
- Ordinary imports of original OneEval BenchInfo, metric registry, parser, general scorer and MetricRunner; real langgraph/langchain dependencies and logger are present. No AST facade or fake state/logger is used by this study.
- MetricRunner Git blob: 4ab430ab3ff60d3e44b34b5777fcfaba9919fa07.
- BenchInfo Git blob: 17e93830cc3ca20090e46da9b3b43500ff08d764.
- All 300 original generated prompt strings exactly equal their authenticated earlier captures.
- Separate data-only verification passed 3,657 identity/count/prompt checks across 1,200 condition records.

The prior holdout artifact was retrieved from ricardofitas/swarm-adaption-hackathon, artifact 14091229651, run 43541759934. Its 12,049,837 bytes match SHA256 45b5eb305790ae8f2bf5ceddc46ddabaf230d8654f4260d092443c008a7ffc2b. The earlier source selection protocol is unchanged.

## Boundary of this claim

This is stronger than an AST-only serializer inspection: the installed generator and original metric modules actually run. It is not full DataFlowEvalTool, graph/serving orchestration or an original application CLI run. The original preprocessing output is reused as an authenticated input rather than regenerated through the eager serving imports.

The serving object is a deterministic fixture at the model interface. Zero provider/model/judge calls occurred. The analysis demonstrates a consequence in the framework's generation-based contract, not official ARC/OpenBookQA likelihood-based acc_norm, which is a different evaluation. Gallery metadata labels the contracts reference_mapped/contract_inferred, smoke_passed=false; no claim is made about deployed use, an externally published score, or undisclosed ordinary runs.

These results support a complementary task/score-consistency failure, not a new empirical capability comparison or a proof that this finding exceeds GAMMAF.

## Files

- verify_component_consequence.py: executable component replay.
- verify_results.py: separate data-only reconciliation.
- results/SUMMARY.json: complete counts, native metric results and module provenance.
- results/CAPTURES.json.gz: full prompt/choice/source-hash ledger.
- results/VERIFICATION.json: reconciliation result.

Run in the prepared environment: venv/bin/python verify_component_consequence.py, then venv/bin/python verify_results.py.

Required inputs are the authenticated original capture archive and extracted capture/ tree, plus unchanged native metric source files from the existing contract-holdout-20261114/source_support.zip.b64. Exact package versions and actual module paths/hashes are recorded in the summary.
