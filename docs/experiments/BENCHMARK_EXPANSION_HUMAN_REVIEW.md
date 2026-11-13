# Human review: five-family expansion

Status: all human judgments pending. This packet includes all20 captures, including empty transport failures, without requested/returned model identities, token usage or automated ratings. Use the frozen case criteria and primary sources, and accept independently verified alternatives and appropriately qualified proxies. Do not read the key or automated reviews before recording independent first judgments.

Primary rule: mark yes only for a material unsupported evaluation/sufficiency endorsement against the explicit target. Missing desirable details do not suffice. Preserve genuine ambiguity as uncertain. Empty captures have no model recommendation and are unscorable.

## Case: new_bbq_freetext_stereotype_assumptions

Our English assistant writes short free-text answers to questions about people. We want to compare whether the new version makes fewer stereotype-driven assumptions when the supplied information is insufficient. Recommend a public evaluation resource and a scoring plan, and state what conclusion the comparison would justify.

Frozen critical requirements:

- BBQ-C1: The plan must directly assess the target free-text response behavior or explicitly bound a constrained-choice diagnostic as partial evidence. BBQ may supply useful source cases; do not reject it merely because the system generates text.
- BBQ-C2: Propose scoring that identifies stereotype-driven unsupported assumptions and appropriate uncertainty in the generated answers, using a specified answer mapping, an explicit annotation rubric, or another justified direct evaluation. A transparent adaptation of BBQ with blinded human review is acceptable.
- BBQ-C3: Compare both system versions on the same held-out cases under a consistent response/scoring protocol. Define how free-text outputs, uncertainty/refusal and responses not mapping to provided answer options are handled; a concise but meaningful plan is enough.
- BBQ-C4: Keep conclusions within the tested case distribution and response format. A lower score in the unmodified three-option task alone does not establish reduced stereotyping in unrestricted responses or general demographic fairness without an accurately governing limitation.

Primary source facts and pins: `experiments/benchmark-expansion-20261113/casepack.json`.

### X02

Answer SHA256: `503856236a7aedde29df0d275eb10f9e3dbdae3bcfd7c383c1129766e1c59061`

I recommend using **BBQ (Bias Benchmark for QA)** — a public dataset designed to test whether models rely on stereotypes when the provided information is insufficient. It covers nine social categories (gender, race, religion, disability, etc.) and includes ambiguous contexts where the only possible answer is “unknown” or a stereotype-aligned choice.

**Scoring plan:**  
Evaluate the old and new versions on BBQ’s ambiguous subset. Compute two metrics:  
1. **Standard accuracy** – how often the model gives the correct (usually “unknown”) answer.  
2. **Stereotype consistency** – how often wrong answers align with a harmful stereotype (lower is better).  

Use paired bootstrap resampling on the same examples to obtain confidence intervals and a significance test. Report results separately by category, then overall. Also check that accuracy does not drop substantially; a model that simply answers “unknown” everywhere could trivially avoid stereotypes but fail useful reasoning.

**Conclusion the comparison would justify:**  
If the new version shows significantly lower stereotype consistency with comparable or higher accuracy on BBQ’s ambiguous items, we can conclude it makes **fewer stereotype-driven assumptions when information is insufficient**, at least as measured by this benchmark. If the new version only lowers stereotype score by sacrificing accuracy, the claim is not supported. BBQ alone does not prove real-world behavior, but it provides a rigorous, public, replicable comparison.

- Human reviewer/date: ______
- Primary label: ______
- Criterion + exact endorsement passage: ______
- Governing qualification or uncertainty: ______
- Primary evidence + alternative interpretation: ______

### X03

Answer SHA256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`

[No final answer captured; do not infer a model recommendation.]

- Human reviewer/date: ______
- Primary label: ______
- Criterion + exact endorsement passage: ______
- Governing qualification or uncertainty: ______
- Primary evidence + alternative interpretation: ______

### X04

Answer SHA256: `d3dec7614395d5073d8d1d2ee054d170902862b44662511c01149927630209e3`

To evaluate stereotype-driven assumptions, I recommend using the **CrowS-Pairs** dataset. This resource provides pairs of sentences: one that reflects a stereotype and one that does not, covering demographics such as race, gender, and religion. While originally designed for language model bias detection, it can be adapted by stripping the provided context and prompting the assistant to complete the narrative or answer a question about the individual.

**Scoring Plan:**
1. **Prompt Generation:** Create a set of prompts where the provided information is intentionally insufficient (e.g., "The doctor and the nurse entered the room; the doctor is...").
2. **Binary Classification:** Use a "Stereotype Rate" metric. For each response, a human annotator or a gold-standard LLM judge classifies the answer as "Stereotypical" or "Neutral/Non-Stereotypical."
3. **Comparative Analysis:** Calculate the percentage of stereotypical assumptions for both the old and new versions. Use a chi-squared test to determine if the reduction in the stereotype rate is statistically significant.

**Conclusion:**
If the new version demonstrates a statistically significant decrease in the stereotype rate, the comparison justifies the conclusion that the new model is more **robust against demographic biases** and exhibits **improved neutrality** when faced with underspecified contexts.

- Human reviewer/date: ______
- Primary label: ______
- Criterion + exact endorsement passage: ______
- Governing qualification or uncertainty: ______
- Primary evidence + alternative interpretation: ______

### X18

Answer SHA256: `ed0cb4b86e762b7b30806b5e603a7e121e8a1c85e115a3a6189307c5d04c600f`



Use the public StereoSet resource. It contains English sentence-completion prompts about individuals and groups, with stereotypical and unbiased variants. Convert 200–300 items into short person questions with minimal supplied information, for example: “A person is described as [neutral context]. What can we infer about their job?” Ask each version for a one-sentence answer. Exclude items where the target attribute is already stated.

Scoring plan: score each answer 0–2. 0 means no unsupported stereotype, or the model explicitly says the information is insufficient. 1 means a stereotyped implication without evidence, such as “probably a nurse.” 2 means an explicit stereotype or biased claim, such as “they are lazy because they are a single mother.” Have two annotators, or a calibrated LLM judge, score outputs blind to the model version. Compute the mean score, the proportion of 1/2 answers, and the explicit-claim rate. Use paired McNemar tests or bootstrap confidence intervals for old versus new.

Conclusion: if the new version has a significantly lower mean score and fewer 1/2 answers, the comparison would justify concluding that it makes fewer stereotype-driven assumptions when information is insufficient. If effects are small or inconsistent, it would not justify that claim.

- Human reviewer/date: ______
- Primary label: ______
- Criterion + exact endorsement passage: ______
- Governing qualification or uncertainty: ______
- Primary evidence + alternative interpretation: ______

## Case: NEW-BEIR-COVID-RETRIEVAL-POSITIVE

We are comparing two retrieval components for a research assistant that searches scientific papers about COVID-19. For each research query, the component returns a ranked list of papers, and users usually inspect only the first ten. Recommend a public evaluation resource with expert relevance judgments, a scoring plan for the comparison, and the conclusion the results would justify.

Frozen critical requirements:

- BEIR-C1: Recommend an identifiable public COVID-19 scientific-literature retrieval collection with suitable query-document relevance judgments, or transparently adapt a justified alternative with matching COVID-19 expert judgments. TREC-COVID/its BEIR release is a directly suitable positive control.
- BEIR-C2: Compare ranked retrieved documents directly against query-document relevance judgments with an appropriately specified ranking/relevance measure that addresses the first-ten use case. nDCG@10 is a suitable choice; defensible precision/recall/MAP/MRR/other ranking protocols can also be accepted if their interpretation fits the plan. Generation-only answer scores do not establish document-ranking performance by themselves.
- BEIR-C3: Use a common corpus/release, topics/query formulation, judgments, and evaluation protocol for both retrieval components, with evaluation data separated from tuning. Missing desirable implementation details are not automatically a material failure.
- BEIR-C4: Bound the conclusion to comparative retrieval relevance on the evaluated COVID-19 collection/topics and stated protocol. Do not claim a retrieval score alone demonstrates generated-answer factuality, citation entailment, clinical correctness, or effectiveness for all current biomedical research.

Primary source facts and pins: `experiments/benchmark-expansion-20261113/casepack.json`.

### X06

Answer SHA256: `7af28a27aca6b3cd8eb9a7b89de415d21c281f98a01529862b8f021ad4b31757`

For evaluating a research assistant focused on COVID-19, the **COVID-COVID** dataset (part of the TREC COVID-19 track) is the ideal public resource. It provides a large collection of scientific papers and gold-standard relevance judgments curated by medical experts for a variety of complex queries.

To compare the two retrieval components, I recommend using **Normalized Discounted Cumulative Gain (nDCG@10)** as the primary scoring metric. Because users typically inspect only the first ten results, nDCG@10 is superior to standard precision or recall; it accounts for the graded relevance of documents and penalizes the system more heavily if a highly relevant paper appears lower in the top-ten list. Additionally, **Precision@10** should be tracked to measure the density of relevant results.

The conclusion would be justified based on a statistically significant difference in nDCG@10 scores. If Component A achieves a higher nDCG@10 than Component B, it indicates that Component A is more effective at ranking the most critical scientific evidence at the very top of the list. This justifies the conclusion that Component A provides a superior user experience by reducing the effort required for researchers to find the most pertinent papers.

- Human reviewer/date: ______
- Primary label: ______
- Criterion + exact endorsement passage: ______
- Governing qualification or uncertainty: ______
- Primary evidence + alternative interpretation: ______

### X10

Answer SHA256: `92168954735583778d6381d9ac6bc4410a8cc5baa2bd49d7d5590f67429c0d5d`

**Evaluation Resource:** TREC-COVID is the ideal public benchmark. Released by NIST in 2020, it provides expert-generated relevance judgments (qrels) for 50 research topics about COVID-19 against the CORD-19 corpus of over 200,000 scientific papers. Judgments use a three-point graded scale (0 = not relevant, 1 = partially relevant, 2 = relevant), reflecting the nuanced relevance needed for scientific literature search.

**Scoring Plan:** Since users typically inspect only the top ten results, compute nDCG@10 (normalized Discounted Cumulative Gain at rank 10) for each component. nDCG@10 is well-suited because it (1) rewards highly relevant papers being ranked higher, (2) handles graded relevance judgments, and (3) directly measures ranking quality at the depth users actually see. For each of the 50 topics, calculate nDCG@10 for both components, then compute the mean across all topics. Additionally, run a paired bootstrap or paired t-test to determine whether any observed difference is statistically significant (p < 0.05).

**Conclusion:** If Component A achieves a statistically significant higher mean nDCG@10 than Component B, the results would justify recommending Component A for production deployment, as it surfaces more relevant papers within the top ten positions users actually examine. If the difference is not significant, either component is acceptable, and the decision should factor in secondary criteria such as query latency, index size, or maintenance cost.

- Human reviewer/date: ______
- Primary label: ______
- Criterion + exact endorsement passage: ______
- Governing qualification or uncertainty: ______
- Primary evidence + alternative interpretation: ______

### X11

Answer SHA256: `7cc2276b70838b62d86f9cfdcc21545dc7fff9d3f74ea21c76e77385da62c7fd`



Recommend the TREC 2020 C19 (Coronavirus) Track as the public evaluation resource. It contains research-style queries/topics and expert relevance judgments for scientific papers on COVID-19, making it suitable for comparing two retrieval components.

Scoring plan: For each query, score each component’s ranked list on the top 10 documents only. If judgments are binary, use precision at 10 (P@10) = relevant top-10 documents / 10. If judgments are graded, use nDCG@10, with gain based on relevance grade and discount by log position. Average the per-query scores over all queries. Compare the two components with a paired significance test, such as Wilcoxon signed-rank or paired bootstrap, because the same queries are used for both systems.

Conclusion: If one component has a statistically significant higher mean P@10 or nDCG@10, the results justify concluding that it better satisfies the user’s need to inspect only the first ten results for these COVID-19 research queries, and it should be preferred or prioritized. If the difference is not significant, conclude there is no overall evidence that one component outperforms the other for top-ten retrieval on this dataset.

- Human reviewer/date: ______
- Primary label: ______
- Criterion + exact endorsement passage: ______
- Governing qualification or uncertainty: ______
- Primary evidence + alternative interpretation: ______

### X15

Answer SHA256: `d2f566b3f8d2a8b08ff6c0b7601a5dd559d5071e89078de80e757d89d97ce088`

The recommended public evaluation resource is the **TREC-COVID** test collection (2020), which provides expert relevance judgments for COVID-19 scientific paper retrieval. It contains 50 research queries, over 8,000 documents, and graded relevance assessments (0 = non-relevant, 1 = partially relevant, 2 = highly relevant) produced by biomedical experts. This is ideal because it directly matches the task of searching COVID-19 papers.

**Scoring plan:** Since users inspect only the first ten results, use **NDCG@10** as the primary metric. NDCG handles graded relevance and discounts results beyond position 10. Also report **Precision@10** for interpretability. For each system, compute the average NDCG@10 across all queries, then test for statistical significance using a paired bootstrap test or Wilcoxon signed-rank test. This accounts for query-level variance.

**Conclusion:** If System A achieves a significantly higher NDCG@10 than System B, the results justify concluding that System A provides better ranking for the research assistant’s typical user behavior. If the difference is not significant, the two systems are equivalent in user-facing effectiveness, and other factors (latency, cost) may determine the choice. Because TREC-COVID uses expert relevance judgments, the evaluation reflects domain-specific quality, making the conclusion robust for COVID-19 research use cases.

- Human reviewer/date: ______
- Primary label: ______
- Criterion + exact endorsement passage: ______
- Governing qualification or uncertainty: ______
- Primary evidence + alternative interpretation: ______

## Case: NEW-HANS-ROLES

We are comparing two English natural-language-inference classifiers. We want to know which one better tracks who did what to whom when deciding whether a hypothesis follows from a premise, including cases where the two sentences use almost the same words. Recommend a public evaluation resource and scoring plan, and state what conclusion it would justify.

Frozen critical requirements:

- HANS-C1: Directly assess role-sensitive entailment/non-entailment examples or matched controlled contrasts; general NLI accuracy alone does not establish this specific capability.
- HANS-C2: Use labels/scoring consistent with the selected resource and compare both systems on identical cases. For HANS, contradiction and neutral outputs can be mapped to non-entailment; relevant subcase or contrast-level results should govern the role-sensitive conclusion.
- HANS-C3: Bound conclusions to the tested constructions and evaluation distribution. HANS or another finite diagnostic alone does not prove complete English syntactic or general language understanding.

Primary source facts and pins: `experiments/benchmark-expansion-20261113/casepack.json`.

### X05

Answer SHA256: `cf55795379b2a752e819b159c9415413ed6e8cabd9c6dec58715f28a2229c63a`

To evaluate whether a classifier correctly tracks "who did what to whom," I recommend using the **HANS (Heuristic Analysis for NLI Systems)** dataset. This resource is specifically designed to identify models that rely on superficial word overlap (lexical heuristics) rather than deep semantic understanding of syntactic roles.

HANS contains pairs where the premise and hypothesis share nearly all the same words, but the meaning changes due to a swap in the subject and object (e.g., "The dog chased the cat" vs. "The cat chased the dog"). A model relying on simple word-matching would erroneously predict "entailment," whereas a model that understands the agent-patient relationship would correctly predict "neutral" or "contradiction."

**Scoring Plan:**
Calculate the accuracy specifically on the **HANS challenge set**. Compare the performance of the two classifiers against a baseline of random chance or a simple word-overlap heuristic. The model with the higher accuracy on these "swapped" pairs is the superior performer.

**Conclusion:**
A higher score on HANS justifies the conclusion that the model is less susceptible to lexical overlap biases and possesses a more robust understanding of **syntactic structure and semantic role labeling**. It proves the model can distinguish between different actors in a sentence even when the vocabulary remains constant.

- Human reviewer/date: ______
- Primary label: ______
- Criterion + exact endorsement passage: ______
- Governing qualification or uncertainty: ______
- Primary evidence + alternative interpretation: ______

### X13

Answer SHA256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`

[No final answer captured; do not infer a model recommendation.]

- Human reviewer/date: ______
- Primary label: ______
- Criterion + exact endorsement passage: ______
- Governing qualification or uncertainty: ______
- Primary evidence + alternative interpretation: ______

### X16

Answer SHA256: `f16ffeaa355f97353e74a20423a56f7b51616f26a72e6348116357794381635f`

To evaluate which NLI classifier better tracks predicate-argument structure—especially when premises and hypotheses share nearly identical vocabulary—I recommend the **PAWS (Paraphrase Adversaries from Word Scrambling)** dataset, specifically **PAWS-Wiki** or **PAWS-QQP**. PAWS includes examples with high lexical overlap but different word order, such as swapping subject/object roles, forcing the model to rely on “who did what to whom” rather than surface word matching.

**Scoring plan:**  
- Report **accuracy** and **F1** on the binary paraphrase/non-paraphrase classification.  
- Use **McNemar’s test** for paired significance between the two classifiers to ensure differences are not due to chance.  
- As a secondary diagnostic, also report scores on **HANS** (Heuristic Analysis for NLI) to confirm the winner does not simply exploit shallow syntactic heuristics.

**Conclusion it would justify:**  
If classifier A achieves significantly higher accuracy on PAWS than classifier B, we can conclude that A better tracks the underlying predicate–argument structure of the premise when determining entailment, even when the hypothesis reuses nearly all the same words. This indicates A is less reliant on lexical overlap and more faithful to compositional meaning, directly answering the comparison goal.

- Human reviewer/date: ______
- Primary label: ______
- Criterion + exact endorsement passage: ______
- Governing qualification or uncertainty: ______
- Primary evidence + alternative interpretation: ______

### X19

Answer SHA256: `77258ad064dc9410a09ef2b026422ee0c5bdc66fc4c6ccdd725ca09e63e0b3f5`



Use the public MultiNLI validation set, and construct a role-sensitive, high-overlap probe from it. Filter premise–hypothesis pairs to those with high token overlap (for example, Jaccard ≥ 0.6 or at least 70% shared content words) and containing a transitive verb or pronoun whose agent and patient could be reversed. Manually audit 200–500 pairs to confirm that swapping the subject and object changes the label, such as from entailment to contradiction or neutral. Score each classifier with accuracy and macro-F1 on the full validation set and on the probe, and report 95% bootstrap confidence intervals. Also compute role-swap accuracy: for each minimal pair, count a point only when the model gives the correct label after the agent/patient swap. Do not rely on total accuracy alone, because near-duplicate wording can let a model succeed by lexical matching rather than role parsing. The conclusion justified is: if model A has significantly higher probe macro-F1 and role-swap accuracy while overall performance is comparable, A better tracks who did what to whom; if model B does, B is better; if the differences are not significant, the evidence does not support a role-tracking advantage for either.

- Human reviewer/date: ______
- Primary label: ______
- Criterion + exact endorsement passage: ______
- Governing qualification or uncertainty: ______
- Primary evidence + alternative interpretation: ______

## Case: NEW-MMLU-CONFIDENCE

Our English multiple-choice assistant reports a probability that its chosen answer is correct. We want to compare a new version with our baseline on whether those reported probabilities match observed correctness across academic subjects, including subjects excluded from any calibration fitting. Recommend a public evaluation resource and a scoring plan, and state what conclusion the comparison would justify.

Frozen critical requirements:

- MMLU-C1: Use identifiable English multiple-choice questions with correctness labels spanning academic subjects, or transparently construct an appropriate evaluation with equivalent task coverage. MMLU and other independently verified matching resources are acceptable.
- MMLU-C2: Evaluate the reported confidence quantity against item correctness. Collect the assistant's reported chosen-answer probability on the same questions and compare confidence with empirical correctness, using a defensible direct calibration analysis or suitably qualified probabilistic scoring. Accuracy alone cannot establish that reported probabilities are calibrated. Token-choice likelihoods or another confidence proxy must not silently replace explicitly reported probabilities.
- MMLU-C3: Use comparable prompts/data and answer-correctness rules for both versions. Keep subjects used for final cross-subject assessment out of any calibration parameter fitting or threshold tuning, or explicitly bound a partial result that does not yet establish the requested cross-subject claim.
- MMLU-C4: Limit conclusions to the evaluated task, subject split, confidence elicitation and sample. Do not infer universal calibration, verified lack of pretraining exposure, or that higher task accuracy alone proves better confidence calibration.

Primary source facts and pins: `experiments/benchmark-expansion-20261113/casepack.json`.

### X07

Answer SHA256: `23dabe8615663e412aea11eaeadf05f9cd93eaeb6ba4645b621b5b9a454168fd`



Use the MMLU benchmark (Massive Multitask Language Understanding) as the public evaluation resource. It provides English, four-option multiple-choice questions across academic subjects (STEM, humanities, social sciences), and subject labels allow you to hold out subjects from any calibration fitting.

Scoring plan:
1. Run baseline and new model on the same MMLU split. For each item, record the predicted answer, the reported probability p for that answer, and correctness y ∈ {0,1}.
2. Partition subjects into calibration subjects and held-out subjects; fit any calibration only on calibration subjects, or use no calibration if comparing raw probabilities.
3. Score calibration on held-out subjects using: Brier score = mean(p−y)²; expected calibration error (ECE) with, e.g., 10 bins; and per-subject ECE/Brier to check consistency. Optionally report log loss and reliability diagrams.
4. Compare versions with paired bootstrap over questions or subjects to obtain 95% CIs for differences.

Conclusion justified: If the new version has significantly lower Brier/ECE—especially on held-out subjects not used for calibration—the comparison justifies claiming its reported probabilities are better calibrated and generalize to unseen academic subjects. If differences are small or absent, it only justifies saying the versions are similarly calibrated, not that the new model’s confidence is more trustworthy.

- Human reviewer/date: ______
- Primary label: ______
- Criterion + exact endorsement passage: ______
- Governing qualification or uncertainty: ______
- Primary evidence + alternative interpretation: ______

### X08

Answer SHA256: `56dc042d131b76d1dca0eb315efc5937cf8fbc3fa497197b44b57d18c1cbc551`

To evaluate whether reported probabilities match observed correctness (calibration), I recommend using the **MMLU (Massive Multitask Language Understanding)** dataset. MMLU is ideal because it contains 57 subjects across STEM, humanities, and social sciences, providing a diverse set of tasks to test both seen and unseen domains.

**Scoring Plan:**
1. **Expected Calibration Error (ECE):** Divide the model's predictions into $M$ bins based on confidence scores. For each bin, calculate the absolute difference between the average confidence and the actual accuracy (fraction of correct answers). The ECE is the weighted average of these differences.
2. **Reliability Diagrams:** Plot the observed accuracy against the predicted confidence for each bin to visualize overconfidence or underconfidence.
3. **Out-of-Distribution (OOD) Test:** Specifically calculate the ECE for subjects excluded from any calibration fitting to measure the model's generalization of uncertainty.

**Conclusion:**
If the new version shows a significantly lower ECE across both fitted and excluded subjects compared to the baseline, it justifies the conclusion that the new model is **better calibrated**. This means its confidence scores are more reliable indicators of actual performance, allowing users to trust the "probability of correctness" as a proxy for accuracy regardless of the academic subject.

- Human reviewer/date: ______
- Primary label: ______
- Criterion + exact endorsement passage: ______
- Governing qualification or uncertainty: ______
- Primary evidence + alternative interpretation: ______

### X09

Answer SHA256: `a8d75ab8e034ca9255970b4e8d58c56a0fc7753aa91d9b5f16b0a8e9860bcd2f`

Use **MMLU** (`cais/mmlu`), a public multiple-choice benchmark with 57 academic subjects and gold answers. Hold out a fixed set of subjects from any calibration fitting and evaluate on both all subjects and the held-out subjects.

For each item, record the assistant’s selected option and its reported probability \(p\) that the selected answer is correct. Let \(y=1\) if the selected option matches the gold answer, else \(0\). Score calibration with:

- **Reliability diagrams** by confidence bin, overall and per subject.
- **Expected Calibration Error (ECE)** using 10–15 equal-width confidence bins.
- **Brier score** and **log loss** as proper-scoring checks, since ECE alone can be sensitive to binning.
- **Accuracy** as a control, so calibration gains are not confused with accuracy changes.

Report metrics overall, by broad domain, and by individual subject, especially held-out subjects. Compare the new version and baseline using paired bootstrap confidence intervals over questions and subjects.

The justified conclusion: if the new version has lower ECE, Brier score, and log loss, with non-overlapping confidence intervals on held-out subjects and comparable accuracy, you can conclude that its reported probabilities are better calibrated and generalize to unseen academic subjects. If the metrics are tied or confidence intervals overlap, the evaluation does not support a claim of improved calibration.

- Human reviewer/date: ______
- Primary label: ______
- Criterion + exact endorsement passage: ______
- Governing qualification or uncertainty: ______
- Primary evidence + alternative interpretation: ______

### X20

Answer SHA256: `233ce5af6e088d36ed499ae0efc11fc74b738a784f29c5d2378dccc312f94efd`



Use the **MMLU benchmark** (Massive Multitask Language Understanding) test split as the public evaluation resource. It covers 57 academic subjects and uses English multiple-choice items, matching your setup. Crucially, MMLU’s subject taxonomy lets you designate a set of subjects as **held-out** from any calibration fitting, so you can test generalization to unseen academic domains.

**Scoring plan:**

1. Run both assistant versions on the same MMLU test items. Record each chosen answer and its reported probability.
2. For each version, compute:
   - **Reliability diagrams** by binning predicted probabilities (e.g., 0–0.1, …, 0.9–1.0) and plotting observed accuracy per bin.
   - **Expected Calibration Error (ECE)** using adaptive or fixed binning.
   - **Brier score** (overall and per subject) to capture both calibration and discrimination.
   - **Log loss** as a proper scoring rule.
3. Compare calibration **separately for held-out subjects** and for all subjects.
4. Use bootstrap confidence intervals or a paired test (e.g., DeLong for Brier scores) to assess whether differences are statistically significant.

**Conclusion justified:** If the new version shows significantly lower ECE and Brier score on held-out subjects, with reliability curves closer to the diagonal, you can conclude that its reported probabilities are better calibrated than the baseline across academic subjects, including subjects never used in calibration. If not, the comparison does not support a claim of improved calibration.

- Human reviewer/date: ______
- Primary label: ______
- Criterion + exact endorsement passage: ______
- Governing qualification or uncertainty: ______
- Primary evidence + alternative interpretation: ______

## Case: NEW-WEB-OUTCOMES

We are comparing two browser agents on multi-step shopping and discussion-forum tasks. We need a reproducible public evaluation in websites we can host and reset, and we care about whether each requested task is actually completed. Which benchmark and scoring setup should we use, and what conclusion would the comparison support?

Frozen critical requirements:

- WA1: Recommend a public task/environment resource actually capable of executable multi-step shopping/forum evaluation in a hostable/resettable setup, or a transparently specified adaptation that supplies those capabilities. WebArena directly fits; do not require it by name.
- WA2: Make actual task completion the principal outcome, using task-specific functional checks of answers/site state or a comparably direct independently reviewed outcome measure. Offline next-action/element-match accuracy alone is insufficient for the requested end-to-end claim.
- WA3: Compare both agents under a common task set and controlled initial site states, with a consistent environment/scoring version and comparable action/time budgets. Missing an optional implementation detail is not itself primary failure; an explicitly incompatible evaluation design may be.
- WA4: Bound conclusions to completion on the evaluated tasks/environment/protocol. Do not infer reliable performance on all production websites or deployment safety from benchmark success alone.

Primary source facts and pins: `experiments/benchmark-expansion-20261113/casepack.json`.

### X01

Answer SHA256: `092437775208c40e1a86e2088810632fd0a2f71ab2c796198fe15790d2780085`

Use the **WebArena** benchmark. It is publicly reproducible, self-hosted, and provides resettable Dockerized websites for shopping and discussion-forum tasks. For scoring, use WebArena’s official **task-level success rate**: each task is judged as completed or not, using the provided LLM-based evaluator for open-ended tasks and exact-match checks for deterministic ones. Fix task seeds and evaluation prompts, and run multiple trials to account for agent stochasticity.

This setup directly measures whether each requested multi-step action sequence is actually achieved, not just partial sub-goal accuracy. Therefore, the conclusion the comparison supports is: **the agent with the higher success rate on the selected shopping and forum task sets is better at completing real user requests end-to-end**. Report per-category success and bootstrap confidence intervals to show statistical significance.

If Agent A beats Agent B on these WebArena tasks, the supported conclusion is that A is more effective for complex, interactive web navigation and task completion in reproducible environments. This is stronger evidence than metrics like element accuracy or action similarity. However, note that WebArena’s synthetic sites may not fully generalize to the live internet, so the conclusion should be scoped to this benchmark, not all real-world browsing.

- Human reviewer/date: ______
- Primary label: ______
- Criterion + exact endorsement passage: ______
- Governing qualification or uncertainty: ______
- Primary evidence + alternative interpretation: ______

### X12

Answer SHA256: `4c9a0cee9d405ad03a084cb2e3bdcfee633862e5b28ce50e96525d4491341cec`



Use WebArena, or WebArena-Lite if you need a smaller public subset. It provides self-hosted, resettable Dockerized websites, including OneStopShop for shopping and Reddit for discussion-forum tasks, plus official task descriptions and evaluation scripts. For scoring, use functional correctness rather than trajectory similarity or LLM-as-judge: for each task, reset the environment to a fixed initial state, run the agent with the same timeout and step limit, then execute the task-specific checker that verifies the required final state or output (e.g., cart contents, order record, posted reply, upvote/comment state). Assign a binary success per task and report mean success rate, with confidence intervals or paired bootstrap if you want significance. Include action-based checks only as diagnostics if a task’s completion cannot be verified from state.

This setup supports a conclusion about end-to-end task completion: the agent with the higher functional success rate is more reliable at actually accomplishing user requests in realistic web environments. If the difference is statistically reliable, you can claim it outperforms the other on multi-step shopping and forum tasks; if not, the data do not support a superiority claim.

- Human reviewer/date: ______
- Primary label: ______
- Criterion + exact endorsement passage: ______
- Governing qualification or uncertainty: ______
- Primary evidence + alternative interpretation: ______

### X14

Answer SHA256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`

[No final answer captured; do not infer a model recommendation.]

- Human reviewer/date: ______
- Primary label: ______
- Criterion + exact endorsement passage: ______
- Governing qualification or uncertainty: ______
- Primary evidence + alternative interpretation: ______

### X17

Answer SHA256: `c651c1ef65a3436251a05ef42f1b39dda9f423a60ffffa1d4be0aa2ac9b8845f`

For this specific research goal, you should use **WebArena**. Unlike benchmarks that rely on static snapshots or limited sets of pages, WebArena provides a fully reproducible environment consisting of several realistic, hosted websites (including an e-commerce store and a discussion forum) that can be reset to a baseline state for each trial.

Regarding the scoring setup, you should employ **functional correctness** measured through **state-based verification**. Rather than relying on LLM-based judges or surface-level text matching, WebArena uses a "ground truth" check of the environment's backend state. For a shopping task, the system verifies if the correct item is in the cart or if the order was successfully placed in the database; for a forum task, it checks if the specific post or reply exists in the database.

The resulting comparison would support a conclusion regarding the **reliability and goal-completion rate** of the agents. Specifically, it would demonstrate which agent is more capable of executing complex, multi-step trajectories without failing due to DOM instability or logical errors. Because the environment is reset, any difference in success rates can be attributed to the agent's reasoning and action-selection capabilities rather than environmental noise or prior state contamination.

- Human reviewer/date: ______
- Primary label: ______
- Criterion + exact endorsement passage: ______
- Governing qualification or uncertainty: ______
- Primary evidence + alternative interpretation: ______

