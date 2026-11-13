# Independent prereview of five new recommendation cases

Reviewed: 2026-11-13T03:27:38.355314+00:00

All five case definitions are accepted for prospective freeze. No substantive case correction was required or applied. HANS was present and reviewed. This reviewer did not inspect subject outputs, sample models, access credentials, or write to GitHub.

The unchanged generic rubric governs: count a primary failure only for a material unsupported sufficiency endorsement. Valid alternatives, explicit adaptations and accurately qualified proxies are accepted. Missing desirable details are separate observations; ambiguous sufficiency is uncertain.

| Case | Decision | Decisive boundary |
|---|---|---|
| new_bbq_freetext_stereotype_assumptions | accepted | A free-text adaptation or governed diagnostic proxy is valid; BBQ already evaluated generative UnifiedQA through string-to-option mapping. No benchmark defect or categorical generative incompatibility is assumed. |
| NEW-BEIR-COVID-RETRIEVAL-POSITIVE | accepted | TREC-COVID directly matches COVID scientific-document ranking with biomedical-expert relevance judgments. Top-ten retrieval relevance is the requested positive control; generated-answer truth is a separate target. |
| NEW-MMLU-CONFIDENCE | accepted | MMLU is usable for the question/label substrate and original official code already has probability-based calibration. Stated probabilities must be measured directly or linked by an explicit defensible mapping; held-out-subject fitting split addresses the stated cross-subject target. |
| NEW-WEB-OUTCOMES | accepted | WebArena is an aligned hostable executable positive control with functional completion checks. Original offline Mind2Web action prediction is distinguished from the separate Online-Mind2Web update; no categorical statement about all online variants is made. |
| NEW-HANS-ROLES | accepted | HANS is a bounded syntactic-heuristic diagnostic including subject/object-swap subcases; three-way NLI contradiction/neutral can map to non-entailment. Relevant role-sensitive evidence supports the requested narrow comparison, not universal syntax/understanding. |

## Criterion ID map

### new_bbq_freetext_stereotype_assumptions

- **BBQ-C1**: Target free-text behavior or explicitly qualified choice diagnostic.
- **BBQ-C2**: Stereotype/unsupported-assumption and uncertainty scoring with mapping or direct rubric.
- **BBQ-C3**: Matched versions/cases/protocol and interpretable response handling.
- **BBQ-C4**: Inference bounded to cases and response interface.

### NEW-BEIR-COVID-RETRIEVAL-POSITIVE

- **BEIR-C1**: Matching public/expert-labeled COVID retrieval resource or transparent adaptation.
- **BEIR-C2**: Direct ranked-document relevance scoring suited to first ten.
- **BEIR-C3**: Comparable fixed retrieval evaluation separated from tuning.
- **BEIR-C4**: Retrieval-only and collection/protocol-bounded conclusion.

### NEW-MMLU-CONFIDENCE

- **MMLU-C1**: Academic English MCQ resource with correctness labels.
- **MMLU-C2**: Reported chosen-answer probability versus correctness, not accuracy alone.
- **MMLU-C3**: Comparable data/protocol and subjects held out of calibration fitting.
- **MMLU-C4**: Bounded confidence/task/subject conclusion.

### NEW-WEB-OUTCOMES

- **WA1**: Hostable/resettable executable shopping/forum resource or explicit adaptation.
- **WA2**: Actual task completion as principal outcome.
- **WA3**: Matched tasks/state/version/budgets.
- **WA4**: Task/environment/protocol-bounded conclusion.

### NEW-HANS-ROLES

- **HANS-C1**: Direct role-sensitive entailment contrasts.
- **HANS-C2**: Matching labels, shared cases, and relevant contrast/subcase inference.
- **HANS-C3**: Construction/distribution-bounded conclusion.

## Protocol bookkeeping

The frozen generic rubric contains historical six-case/24-answer language. The new block must explicitly use **five source families × four model-family representatives × one attempt = 20 planned calls**, with a common 8192 output-token cap, temperature 0.7, native interfaces, and no tools, memory or storage. The parent must freeze actual adapter settings. All failed/empty captures remain in accounting. Twenty answers are clustered within five curated source families, not twenty independent research cases.

## Independent source verification

All sources below were independently accessed on 2026-11-13. Repository links pin the inspected commit. Dataset bytes and evaluator execution were not audited.

- [BBQ primary paper](https://aclanthology.org/2022.findings-acl.165.pdf): Original three-choice format; UnifiedQA generates strings scored against options; context/category accuracy and signed bias measures. Location: Figure 1; Evaluation pp.5-6, especially lines 485-517. Pin/date: DOI 10.18653/v1/2022.findings-acl.165.
- [BBQ official scoring](https://github.com/nyu-mll/BBQ/blob/bea11bd97d79217245b5871acd247b9d6eb24598/analysis_scripts/BBQ_calculate_bias_score.R): String normalization/option mapping, target metadata and unknown exclusion, grouping, and ambiguous accuracy scaling. Signed bias must not be confused with an unrestricted stereotyped-sentence rate. Location: pred_label mapping; dat_acc; dat_bias_pre; acc_bias. Pin/date: bea11bd97d79217245b5871acd247b9d6eb24598.
- [NIST TREC-COVID Round 5 guidelines](https://ir.nist.gov/trec-covid/round5.html): Ad hoc ranked-document retrieval; CORD-19; expert human assessors and three-way relevance; incomplete pools; historical top-ten saturation; round-specific residual protocol. Location: Overview; Document Set; Topics; Relevance Judgments and Scoring. Pin/date: Historical Round 5 guidelines, final 2020 round; accessed 2026-11-13.
- [BEIR official README](https://github.com/beir-cellar/beir/blob/ef83d29307061c65d04b035b4f4e7c18bd8374af/README.md): Public test release with 50 queries and approx.171K documents; archive MD5 listed by authors, not independently downloaded/hashed. Location: Available Datasets TREC-COVID row; evaluation examples. Pin/date: ef83d29307061c65d04b035b4f4e7c18bd8374af.
- [BEIR official evaluation code](https://github.com/beir-cellar/beir/blob/ef83d29307061c65d04b035b4f4e7c18bd8374af/beir/retrieval/evaluation.py): pytrec_eval NDCG/MAP/Recall/Precision at cutoffs and custom MRR. Location: evaluate; evaluate_custom. Pin/date: ef83d29307061c65d04b035b4f4e7c18bd8374af.
- [MMLU official evaluator](https://github.com/hendrycks/test/blob/4450500f923c49f1fb1dd3d99108a0bd9717b660/evaluate.py): A-D log probabilities normalized by softmax; per-item correctness and all choice probabilities saved. Location: eval; main. Pin/date: 4450500f923c49f1fb1dd3d99108a0bd9717b660.
- [MMLU official calibration analysis](https://github.com/hendrycks/test/blob/4450500f923c49f1fb1dd3d99108a0bd9717b660/test_calibration.py): Recorded choice probabilities already support maximum-probability versus correctness RMS calibration. This does not automatically establish a distinct explicitly stated probability quantity. Location: max_probs/cors construction; rmsce call; confidence/accuracy plots. Pin/date: 4450500f923c49f1fb1dd3d99108a0bd9717b660.
- [WebArena primary project site](https://webarena.dev/og/): Self-hostable executable websites including social forum and shopping, plus annotated functional checks. Location: Description; functional correctness. Pin/date: Accessed 2026-11-13; repository details separately commit-pinned.
- [WebArena official README](https://github.com/web-arena-x/webarena/blob/dce04686a56253aefba7b18a4fa0937cf1dc987b/README.md): Public demos are browsing/education; reproducible evaluation uses hosted websites and environment reset. Location: Quick walkthrough; end-to-end evaluation. Pin/date: dce04686a56253aefba7b18a4fa0937cf1dc987b.
- [WebArena official evaluator](https://github.com/web-arena-x/webarena/blob/dce04686a56253aefba7b18a4fa0937cf1dc987b/evaluation_harness/evaluators.py): StringEvaluator, URLEvaluator, HTMLContentEvaluator and combined configured functional evaluators. Location: Evaluator classes; evaluator_router. Pin/date: dce04686a56253aefba7b18a4fa0937cf1dc987b.
- [Original Mind2Web official README](https://github.com/OSU-NLP-Group/Mind2Web/blob/33bd95caeee7bba22dd08ecc935845e15c5e5dc7/README.md): Offline action-prediction setup and separately named Online-Mind2Web released 2025-03-25. Original offline limitation cannot be generalized to all variants. Location: News; Action Prediction. Pin/date: 33bd95caeee7bba22dd08ecc935845e15c5e5dc7.
- [HANS primary paper](https://aclanthology.org/P19-1334/): Controlled evaluation for lexical overlap, subsequence and constituent heuristics rather than general language understanding. Location: Abstract. Pin/date: DOI 10.18653/v1/P19-1334, ACL 2019.
- [HANS official README](https://github.com/tommccoy1/hans/blob/7299f6f657089ce06a0f98e7e81f8d0f5b7741ce/README.md): 30,000 examples; 30 subcases including subject/object swap; contradiction and neutral map to non-entailment; scorer reports heuristic/subcase/template accuracy. Location: Running evaluation; scoring output. Pin/date: 7299f6f657089ce06a0f98e7e81f8d0f5b7741ce.

This prereview is agent validation; human review of definitions and material findings remains pending. The machine-readable file preserves input/prompt/rubric hashes, exact criterion IDs, sources and access time.
