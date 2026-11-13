# Actual-run diagnostic of unsupported equivalence advice

Prepared on 13 November 2026. No candidate retrieval metric or comparative outcome has been computed. Root must publish the exact protocol, evaluator and source pins before comparative execution.

This route quantifies the consequences of the observed advice to treat a nonsignificant comparison as functional equivalence. It uses authentic archived retrieval outputs. It does not by itself establish a new statistical result, an intrinsic benchmark defect, actual user adoption, cost-based system selection, or GAMMAF-level novelty.

## Fixed sources and candidate pool

The official NIST Round 5 index lists 126 submitted runs. All 126 URLs were selected before any retrieval scoring, with no score-report or ranking-based selection. HEAD requests succeeded for every URL. All 126 gzip files and the matching residual qrels have now been downloaded successfully: 93,208,587 bytes in total, below the 100 MB source budget. Every run structurally contains all 50 topics; short lists would still be retained and scored canonically.

The source registry and receipt preserve compressed and decompressed SHA256 hashes, public release URLs, ETag/Last-Modified where supplied, row counts and topic IDs. These are byte pins for public NIST endpoints, not invented Git dataset revisions. Download failures would remain operationally missing systems, not synthetic zero-performing runs.

The first draft mistakenly proposed excluding short or topic-incomplete files. Before downloading or scoring runs, root required retention of all planned runs. The amended registry preserves its earlier hash and all 126 unchanged candidate URLs. Missing topics and missing retrieval ranks use canonical zero/padding behavior; weak systems are never dropped.

## The residual/Complete distinction

These archived submissions were evaluated after previously judged documents were removed. The matching file is `qrels-covid_d5_j4.5-5.txt`, with 23,151 judgments. The larger cumulative TREC-COVID Complete qrels are a different evaluation collection; NIST states that no official submissions correspond to that complete collection.

The current Q55/Q57 advice does not explicitly combine those archived residual runs with Complete qrels. A targeted inspection of Anserini code also found the two evaluation paths separated correctly. Therefore such a mismatched-qrels replay would be a diagnostic created by us, not a discovered error in those actual workflows. The negative provenance result is retained in `workflow_provenance.json`.

## Scoring

Use a byte-pinned release of the official `usnistgov/trec_eval` implementation, compiled without metric modifications. Primary metric: `ndcg_cut.10`. The secondary `P.10` output is descriptive and cannot replace the primary metric after results.

Canonical ordering, tie handling, relevance gains, incomplete judging and missing-query behavior are delegated to the pinned scorer, with exact command outputs retained. The CLI prints four decimal places per topic; those exact values enter analysis. Per-topic rounding is at most 0.00005, and the paired mean-difference rounding bound is at most 0.0001. Preserve the canonical overall means separately. No precision patch is made.

## Test fidelity and uncertainty

The observed answers offer Wilcoxon or bootstrap tests across all 50 topics. Primary replay therefore uses the offered Wilcoxon branch on all 50 topics, with SciPy 1.17.0: two-sided, `method='auto'`, `zero_method='wilcox'`, no continuity correction. Exact four-decimal scores are converted to integer units before subtraction, preventing spurious floating-point tie distinctions. An all-zero difference vector receives p=1. Nonzero sample counts and identical metric vectors remain visible.

This tests symmetry of paired score differences about zero; it does not test practical equivalence. The exact/asymptotic handling is the pinned library's deterministic rule, with small-sample and tie limitations disclosed. A shared-draw paired sign-flip test is a separately registered sensitivity, never a substitute selected after inspecting outcomes.

For every pair, paired stratified bootstrap intervals describe uncertainty in mean nDCG differences. The interval frontier is `max(abs(lower), abs(upper))`: the smallest symmetric margin containing that conditional interval. No externally justified universal practical-equivalence margin is available, so no margin is invented and no practical-equivalence conclusion is asserted from this frontier.

All 7,875 planned pairs remain visible. Nonsignificant identical-vector pairs are reported separately; duplicate or degenerate metric outcomes cannot silently inflate the interpretation of impact. Shared runs, teams and topics mean these pairs are not independent experimental replications.

## Independent-topic diagnostic

A fixed, score-blind split assigns 25 discovery and 25 confirmation topics, stratified by topic-introduction era. Discovery counts are 17 from topics 1–35, five from 36–45, and three from 46–50, using Python Random seed 2026111340. Exact IDs are in the protocol.

The split is secondary. It does not pretend to execute the original all-50-topic advice literally, and it does not establish held-out model training or future deployment generalization. For every discovery-nonsignificant pair, report the complete distribution of confirmation differences and interval frontiers, plus all pair rows and a declared multiplicity sensitivity. Zero, tie, opposite-direction and null results remain in the record. Actual latency/cost data and selection regret are not available.

## Execution and reproducibility

No scoring occurs until root supplies a real published freeze commit/time and the exact protocol hash to the gate-enforcing evaluator. Source checksums and the evaluator/scorer hashes must all match. The official scorer's fixture tests and synthetic analysis fixtures may run before this gate; they are not candidate-performance results.

Publish small protocols, code, receipts and negative provenance records. The public raw source cache is reproducible from its exact URL/hash receipt; a retrieval performance matrix should only be added after the separate freeze. Any result from this route remains a bounded empirical illustration of a known inferential error unless additional evidence demonstrates a stronger contribution.
