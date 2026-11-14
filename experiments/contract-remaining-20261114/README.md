# Remaining captured split audit

This is a post-discovery diagnostic extension, frozen at private commit 2132ce543650e6d89bb3461c44ba2c6b2a9c8c34 before execution. The first 100 source indices per benchmark from the prior prospective trial are excluded. The unchanged checker and the already reviewed trim-only adapter are applied to all remaining records.

27,346 new records completed with zero model requests and zero source acquisition requests. Independent checks confirmed source bytes, exact disjoint coverage, question and option binding, gold alignment, and source-bound repairs. ARC-Challenge fails on all 1,072 additional rows; OpenBookQA on all 400. Combined with the prior sample, this covers every captured row in those splits (1,172 and 500 respectively). MMLU (13,942 additional) and MMLU-Pro (11,932 additional) pass the measured invariants with the fixed adapter. Literal untrimmed comparison generates 34 and 135 additional false alerts; these are audit-adapter behavior, not new upstream faults. All source-bound repairs pass the measured invariants.

No external run or published score affected by these exact defects has been verified. No new model inference was performed. These four selected contracts do not estimate framework-wide or deployment prevalence.

## Reproduction

The archive includes original source data, selected remaining indices, native and reviewed checker inputs, native preprocessed rows, measured results, and pinned support source. Re-execute with pandas and numpy installed:

    python run_remaining.py BASE_PROSPECTIVE_PACKAGE OUTPUT_DIRECTORY

BASE_PROSPECTIVE_PACKAGE is the extracted OneEval_validacao_prospetiva_4_benchmarks_20261114.zip. OUTPUT_DIRECTORY must contain the supplied PROTOCOL.json. It has no model or network backend. To independently verify this archive, extract that original package and run:

    python verify_remaining.py BASE_PROSPECTIVE_PACKAGE

The originally frozen protocol, original execution log, and operational import-order correction are preserved. Reproduction overwrites only the chosen output work directory.
