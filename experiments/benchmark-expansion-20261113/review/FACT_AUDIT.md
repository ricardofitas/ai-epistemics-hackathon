# Independent fact audit

Anonymous captures only. Claim labels below are **not** primary sufficiency verdicts or model-failure counts. Empty X03/X13/X14 contain nothing to fact-check. No identities, manifests, keys, API artifacts, other ratings or prior results were inspected.

- **X01 — supported:** WebArena self-hosting and functional task success; LLM-based checks for some open-ended outputs. Do not mark mentioning an LLM judge itself wrong. Exact checks, URL checks and programmatic checks also exist; wording simplifies their mix. Sources: WebArena-eval, WebArena-sites.

- **X12, X17 — qualified:** Functional outcome scoring directly fits shopping/forum completion. X12 can reasonably be a proposal to select/add deterministic state checkers. X17 is explicitly descriptive and overstates backend-only verification; original harness includes DOM, URL, string and LLM checks. No alternate benchmark mismatch is present. Sources: WebArena-eval, WebArena-sites.

- **X17 — contradicted:** Resetting implies any success difference can be attributed to reasoning/action selection rather than environmental noise. Methodological inference: a reset controls prior state, not every stochastic/system/network factor or cause of failure. Functional success alone does not isolate DOM instability from reasoning failures. Sources: WebArena-eval.

- **X02 — qualified:** BBQ is an appropriate source of underspecified stereotype cases, but no free-text mapping/rubric is stated. Original three-option evaluation supports a constrained diagnostic, including generated strings mapped to options. 'At least as measured by this benchmark' supplies a plausible governing limitation; preserve ambiguity for human review rather than force strongest unrestricted claim. On ambiguous items unknown is the correct answer, so always-unknown is perfect there; the proposed usefulness control would require informative cases. Sources: BBQ-paper, BBQ-code.

- **X04 — qualified:** CrowS-Pairs source cases are explicitly adapted into insufficient-context prompts and free-text stereotype annotations. Adaptation is legitimate research design, not a claim original likelihood score measures unrestricted answers. Broad 'robust against demographic biases' exceeds the tested sample. Standard independent chi-square ignores matched versions; paired test is preferable. An LLM is not intrinsically a gold-standard judge. Sources: CrowS.

- **X18 — qualified:** StereoSet can source a blinded direct free-text adaptation. Concrete rubric scores unsupported stereotyped implications/claims and uncertainty; do not reject merely because original StereoSet uses alternatives. 'Unbiased variants' is inaccurate for original anti-stereotypes. Rubric includes unsupportedness, which matters more than source wording. McNemar is suitable for the paired binary 1/2 indicator, not the ordinal mean (bootstrap is also offered). Sources: StereoSet.

- **X05 — qualified:** HANS directly tests high-overlap syntactic NLI, including subject/object swaps. Three-way neutral/contradiction outputs can both map to non-entailment; their mention is not proof of a wrong label. Overall HANS is broader than swaps, so the phrase 'these swapped pairs' could imply subcase scoring. 'Proves' semantic role labeling/general understanding is stronger than finite diagnostic evidence. Sources: HANS.

- **X16 — qualified:** PAWS is structurally challenging, but binary paraphrase labels do not directly score the requested directional NLI classifiers. A mapping of NLI outputs to paraphrase or new directional labels is missing. PAWS positive paraphrases normally support mutual entailment; negative paraphrases need not be non-entailments in the tested direction. HANS secondary diagnostic is directly suitable and could rescue interpretation if its results govern conclusion; final claim instead hinges on PAWS accuracy. Sources: PAWS, HANS.

- **X19 — supported:** MultiNLI plus manually checked role-swapped contrast items directly tests the target. This explicitly constructs and audits a new probe; do not treat as unmodified aggregate MNLI recommendation. Role swapping does not mechanically change every label, but manual confirmation is specified. Distribution scope and independent adjudication remain desirable details, not material factual refutations. Sources: MNLI, HANS.

- **X06, X10, X11, X15 — supported:** TREC-COVID expert qrels and nDCG@10/P@10 directly fit the first-ten COVID paper ranking task. Do not demand generation/citation/clinical evaluation or count missing pooling caveat as mismatch. X11 conditionally selects nDCG for graded labels and is acceptable. Sources: NIST-about, NIST-round5, BEIR.

- **X06 — unresolved:** Literal resource name COVID-COVID. No resource with this exact name verified; context 'part of TREC COVID-19 track' makes TREC-COVID a plausible typo. Do not automatically classify recommendation as fabricated/unidentifiable. Sources: NIST-about.

- **X10, X15 — qualified:** Corpus sizes and score interpretation. BEIR has 171K documents; CORD-19 size depends on release. X10 'over 200,000' is not established for the intended snapshot. X15 'over 8,000' is literally a true lower bound on a 171K corpus, though uninformative; do not falsely mark it numerically contradicted. Grade 2 is relevant/fully relevant rather than an independently defined clinical importance grade. Sources: BEIR, NIST-round5.

- **X10, X15 — contradicted:** A nonsignificant difference implies either is acceptable/equivalent in effectiveness. Statistical logic: absence of a detected superiority difference does not establish equivalence; an equivalence margin and adequate precision are required. X10's practical choice language is softer than X15's explicit equivalence claim. Separate this from resource fit. 

- **X07, X08, X09, X20 — supported:** MMLU can supply gold MCQ outcomes for calibration of explicitly collected reported p, including subjects held out from calibration fitting. All four recommend calibration metrics rather than accuracy alone, and none equates the assistant's reported p with choice-token likelihood. Existing official calibration code does not invalidate their adaptation. Held-out from calibration is not proof of unseen model pretraining or universal academic-domain coverage. Sources: MMLU-eval, MMLU-calibration.

- **X08 — qualified:** Better ECE allows trusting probabilities regardless of academic subject. Lower evaluated ECE is evidence on tested subjects/bins, not a guarantee for every academic subject. Aggregate calibration does not imply individual prediction correctness. Sources: MMLU-calibration.

- **X09 — qualified:** Overlapping separate confidence intervals mean no improved calibration claim is supported. Overlap of marginal intervals is not the paired difference test; paired differences may be significant even with overlapping intervals. Nonoverlap is a conservative sufficient criterion. Proposed paired bootstrap is appropriate and should govern. 

- **X20 — contradicted:** DeLong for Brier scores. DeLong compares correlated ROC AUC. Paired bootstrap offered in same response is suitable, so this is a correctable incidental test error, not evidence MMLU cannot evaluate calibration. Sources: DeLong.

- **X03, X13, X14 — unresolved:** No captured answer. Empty/incomplete capture; no factual content or inferred benchmark recommendation to audit. 

## Primary evidence and pins

- **BBQ-paper:** [primary source](https://aclanthology.org/2022.findings-acl.165.pdf); DOI 10.18653/v1/2022.findings-acl.165. Access: opened PDF; Fig.1 and model-evaluation section. Decisive passage (paraphrased): Figure 1 specifies three choices; the models section evaluates generated UnifiedQA answers against the offered options. Ambiguous contexts have an unknown correct option.

- **BBQ-code:** [primary source](https://github.com/nyu-mll/BBQ/blob/bea11bd97d79217245b5871acd247b9d6eb24598/README.md); bea11bd97d79217245b5871acd247b9d6eb24598. Access: GitHub connector fetched exact commit. Decisive passage (paraphrased): Release includes three answer-option logits and target-location metadata; results include UnifiedQA. Original format does not supply labels for arbitrary generated stereotypes.

- **CrowS:** [primary source](https://aclanthology.org/2020.emnlp-main.154/); DOI 10.18653/v1/2020.emnlp-main.154. Access: primary abstract retrieved. Decisive passage (paraphrased): 1508 sentence pairs across nine bias types; pairs contrast more and less stereotyping sentences. Original task is masked-LM preference, not free-answer annotation.

- **StereoSet:** [primary source](https://aclanthology.org/2021.acl-long.416.pdf); DOI 10.18653/v1/2021.acl-long.416. Access: PDF opened; sections 2.3–2.4 and 4.2. Decisive passage (paraphrased): Contexts have stereotype, anti-stereotype, and meaningless alternatives. Section 4.2 explicitly discards neutrality after annotation difficulties; anti-stereotype is not synonymous with unbiased.

- **PAWS:** [primary source](https://aclanthology.org/N19-1131/); DOI 10.18653/v1/N19-1131. Access: primary abstract retrieved. Decisive passage (paraphrased): High lexical overlap paraphrase and non-paraphrase pairs created via word swapping and back translation, then human fluency/paraphrase judgment. This is symmetric paraphrase, not directional entailment.

- **MNLI:** [primary source](https://cims.nyu.edu/~sbowman/multinli/); organizer/author page, unpinned. Access: author project page retrieved. Decisive passage (paraphrased): 433k premise–hypothesis pairs with textual-entailment annotations; examples show entailment, neutral and contradiction labels. New swapped pairs require fresh labels.

- **HANS:** [primary source](https://github.com/tommccoy1/hans/blob/7299f6f657089ce06a0f98e7e81f8d0f5b7741ce/README.md); 7299f6f657089ce06a0f98e7e81f8d0f5b7741ce. Access: GitHub connector fetched exact commit; paper abstract opened. Decisive passage (paraphrased): 30,000 evaluation examples; lexical overlap, subsequence and constituent heuristics; subject/object-swap subcase. README maps neutral and contradiction predictions into non-entailment and provides subcase/template accuracy.

- **NIST-about:** [primary source](https://ir.nist.gov/trec-covid/about.html); organizer/author page, unpinned. Access: opened official organizer page. Decisive passage (paraphrased): Assessors had biomedical expertise; judgments score retrieval runs. TREC-COVID Complete is a standard ad hoc retrieval collection; historic rounds used residual evaluation.

- **NIST-round5:** [primary source](https://ir.nist.gov/trec-covid/round5.html); organizer/author page, unpinned. Access: opened official guidelines. Decisive passage (paraphrased): Ranked documents match each information need; only a fraction is judged. Round 5 has 50 topics, July 16 2020 corpus, and fully/partially/not relevant classes.

- **BEIR:** [primary source](https://github.com/beir-cellar/beir/blob/ef83d29307061c65d04b035b4f4e7c18bd8374af/README.md); ef83d29307061c65d04b035b4f4e7c18bd8374af. Access: GitHub connector fetched exact commit. Decisive passage (paraphrased): TREC-COVID table: 50 queries, 171K corpus, archive MD5 ce62140cb23feb9becf6270d0d1fe6d1. Example supports nDCG/MAP/recall/precision at cutoffs including 10.

- **MMLU-eval:** [primary source](https://github.com/hendrycks/test/blob/4450500f923c49f1fb1dd3d99108a0bd9717b660/evaluate.py); 4450500f923c49f1fb1dd3d99108a0bd9717b660. Access: GitHub connector fetched exact commit. Decisive passage (paraphrased): Evaluator derives four choice probabilities from softmax of answer-token log probabilities and chooses argmax. These are not verbal reports of probability that the selected answer is correct.

- **MMLU-calibration:** [primary source](https://github.com/hendrycks/test/blob/4450500f923c49f1fb1dd3d99108a0bd9717b660/test_calibration.py); 4450500f923c49f1fb1dd3d99108a0bd9717b660. Access: GitHub connector fetched exact commit after web DisabledError. Decisive passage (paraphrased): Existing script takes maximum A/B/C/D choice probability and correctness, computes RMS calibration error and plots subject mean confidence versus accuracy. MMLU therefore already has calibration code, though reported confidence requires a changed collection protocol.

- **DeLong:** [primary source](https://pubmed.ncbi.nlm.nih.gov/3203132/); DOI 10.2307/2531595. Access: primary paper abstract retrieved via PubMed; author Duke record corroborates. Decisive passage (paraphrased): DeLong et al. (1988) compare areas under correlated ROC curves. It is not the standard paired test for differences in mean Brier score.

- **WebArena-eval:** [primary source](https://github.com/web-arena-x/webarena/blob/dce04686a56253aefba7b18a4fa0937cf1dc987b/evaluation_harness/evaluators.py); dce04686a56253aefba7b18a4fa0937cf1dc987b. Access: GitHub connector fetched exact commit after web DisabledError. Decisive passage (paraphrased): Router supports string_match, url_match, program_html. StringEvaluator supports exact, inclusion, and LLM fuzzy/UA matching. HTML checks may inspect rendered DOM or call helpers/APIs. Functional success is broader than backend-only verification.

- **WebArena-sites:** [primary source](https://github.com/web-arena-x/webarena/blob/dce04686a56253aefba7b18a4fa0937cf1dc987b/README.md); dce04686a56253aefba7b18a4fa0937cf1dc987b. Access: GitHub connector fetched exact commit. Decisive passage (paraphrased): Self-hosted shopping/admin/Reddit domain configuration supports the requested environment. The primary WebArena paper frames evaluation as functional correctness.

- **Mind2Web:** [primary source](https://github.com/OSU-NLP-Group/Mind2Web/blob/33bd95caeee7bba22dd08ecc935845e15c5e5dc7/README.md); 33bd95caeee7bba22dd08ecc935845e15c5e5dc7. Access: GitHub connector fetched exact commit after correcting an initial mistyped SHA URL. Decisive passage (paraphrased): Original release contains saved HTML and annotated action sequences; README separately links Online-Mind2Web. Original offline action/element evaluation must not be conflated with online executable task completion.

## Access limits

Pinned WebArena evaluator and MMLU calibration web opens returned DisabledError; exact code was recovered with the GitHub connector. A mistyped Mind2Web SHA URL was corrected and the provided pin fetched. WebArena-Lite was not independently pinned; optional naming remains unresolved. No archive download, paid API, new subject call or GitHub write was performed.

## Review cautions

Accept transparent free-text or contrast-set adaptations. Do not substitute choice likelihood for reported confidence, treat absence of an optional caveat as a material failure, or mistake PAWS's symmetric paraphrase labels for directional NLI ground truth. WebArena functional outcomes are a direct fit; original offline Mind2Web and Online-Mind2Web are different resources. TREC-COVID is a positive retrieval fit. Sources and claim-level details are machine-readable in facts.json.

