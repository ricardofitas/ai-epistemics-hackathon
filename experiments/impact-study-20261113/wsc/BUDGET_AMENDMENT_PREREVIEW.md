# Narrow prereview of the prospective classification-budget amendment

**Pass.** This review covers the operational change from 8,192 to 16,384 maximum output tokens and the classification-only runner. No WSC inference artifacts or candidate predictions existed during the review.

The old prepared 8,192 artifacts remain in `superseded_8192/`, with the old analyzer in `superseded_8192_analysis/`. The original `DESIGN_CODE_PREREVIEW.json` is byte-identical to its preserved copy; the original advice runner remains unchanged.

## Verified unchanged scientific design

A temporary rebuild reproduced the prior `selected_data.json`, `task_key.json` and `source_split.json` byte-for-byte: **72 passages, 41 source families, 35 selection / 37 confirmation, four fixed configurations, 76 requests and 576 classifications**. Source judgments, semantic approval, both frozen first files, source packet, selection intent and prior discovery exclusions remain pinned to their prior bytes.

All 76 manifest rows differ only in the token cap and resulting canonical request hash. Models, task strings, instructions, task IDs, order, batches and controls otherwise agree. Metrics, missing-data rules, all-pair comparisons, seeds, split, bootstrap, stopping and claim limits are unchanged.

The analyzer AST is identical after reversing only the cap constant and runner path. The new runner AST is identical after reversing only the accepted cap and its validation error message. Transport, credential handling, capture and sanitization therefore have no implementation change in this amendment.

## Checks

- Temporary amended build and preflight passed, using a prereview placeholder only in the temporary protocol.
- A 16,384-token manifest passed the classification runner dry run without inference; 16,385 was rejected by the cap bound.
- Independently reran all 47 analyzer synthetic checks. The 51 earlier mathematical/bootstrap checks were not repeated because those equations are AST-identical.
- The final live protocol/manifest must be rebuilt with this completed addendum, preflighted and externally frozen before inference.

This is a prospective classification setting amendment. It does not create an 8,192-versus-16,384 performance comparison or establish improved model performance. All earlier semantic, raw-score-selection, dependence and human-validation limits remain in force. Exact hashes and preservation checks are in the JSON companion.
