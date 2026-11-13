# Bounded factual audit

All 24 open-study responses were inspected. No direct factual contradiction was confirmed in the benchmark and source assertions checked. This is separate from recommendation quality and assigns no primary ratings.

Only review_packet.jsonl and casepack.json were read as local inputs. No manifest, key, rating file or subject history was read. Primary papers, official repositories and release documentation were consulted; casepack assertions were not treated as independent verification.

Coverage includes HumanEval/HumanEval+/MBPP+/EvalPlus and pass@k; SWE-bench/Verified and human-time source claims; ALCE citation metrics and SciFact; WMT20 collection dates and scoring; MATH/PRM800K process claims; and ImageNet-C corruption coverage and mCE. Pure proposed methods (blinding, confidence intervals, new rubrics and study endpoints) are excluded from historical-fact checking.

The audit is bounded. It does not validate the proposed experiments, prove uncontaminated data, run benchmark implementations, or provide exhaustive proof of every sentence. All exact passages below are copied from response text and may contain adjacent methodological material.

## Unresolved and interpretive qualifications

- F16: PRM800K generation provenance is verified; actual distribution difference from unspecified assistants is not established. No contradiction is available.
- F01: WMT20 source dates are explicitly September–November 2019; recollected uncertainty is not an error. The exact installed SacreBLEU data alias was not executed; direct dataset-code retrieval failed.
- F09: HumanEval tests are public. B14’s “hidden tests” can mean hidden from generation; it does not explicitly assert unpublished tests.
- F05: B20 should label raw error versus normalized mCE clearly in implementation; its explicit AlexNet-normalized mCE statement is correct.
- ALCE adaptations are not the paper’s exact metrics; the responses explicitly propose adapted/custom scoring rather than asserting formula identity.

## Grouped claims and exact response passages

### F01 — WMT20/newstest2020 identity, English→German direction and late-2019 online-news recollections

Status: **supported**. Confirmed error: **no**.

Supported: official source-news window is September–November 2019. Qualified recollection and requests to verify it are not errors.

Qualification: Exact installed-version test downloads and en-de alias were not executed; registry supports wmt20, and official release supports the direction.

Sources: [wmt_task](https://www.statmt.org/wmt20/translation-task.html), [wmt_findings](https://aclanthology.org/2020.wmt-1.1.pdf), [sacre_datasets](https://github.com/mjpost/sacrebleu/blob/master/DATASETS.md).

**B01**

> **Benchmark and scoring.** Use WMT20’s English→German news translation test set, `newstest2020` (SacreBLEU: `wmt20`, `en-de`), subject to checking article dates. I recall it as the relevant candidate for late-2019 online news, but am unsure of exact date coverage. Score detokenized outputs against the official reference using SacreBLEU: case-sensitive BLEU with `13a` tokenization, plus chrF. Record metric signatures, package version, and test-set identity.

**B04**

> Use **WMT 2020 news translation, English→German (`newstest2020`)** as the leading public candidate. I recall its material includes late-2019 online news, but am unsure of the exact collection window. Verify publication dates and English-source provenance in the official release. The benchmark year alone does not establish article dates.

**B11**

> Use **WMT20’s English→German news test set, `newstest2020`**, as the first public candidate. I recall its collection being associated with late 2019, but am uncertain about the exact publication window. Verify dates in the official documentation before claiming a temporal match.

**B17**

> **1. Benchmark and scoring.** Use WMT20’s English-to-German news test set, **newstest2020**. My recollection is that its news was collected in late 2019; verify dates in the official task documentation before use. Do not choose newstest2019 based on “2019.” Use the official English source and German reference files. Score detokenized system outputs with sacreBLEU: case-sensitive corpus BLEU with tokenizer `13a`, plus chrF++ as a secondary measure. Record the full metric signatures, package version, reference selection, and preprocessing.

### F02 — SacreBLEU detokenized, case-sensitive BLEU/13a; chrF/chrF2/chrF++; signatures

Status: **supported**. Confirmed error: **no**.

All named scoring options exist. chrF2 uses beta=2; chrF++ uses word n-grams. Suggested document bootstrap is a protocol recommendation, not an assertion that the default CLI clusters documents.

Sources: [sacrebleu](https://github.com/mjpost/sacrebleu), [post](https://aclanthology.org/W18-6319/), [chrf](https://aclanthology.org/W15-3049/).

**B01**

> **Benchmark and scoring.** Use WMT20’s English→German news translation test set, `newstest2020` (SacreBLEU: `wmt20`, `en-de`), subject to checking article dates. I recall it as the relevant candidate for late-2019 online news, but am unsure of exact date coverage. Score detokenized outputs against the official reference using SacreBLEU: case-sensitive BLEU with `13a` tokenization, plus chrF. Record metric signatures, package version, and test-set identity.

**B04**

> Freeze both systems, exclude evaluation data from training/tuning, and use identical sources and references. Score detokenized outputs with **SacreBLEU corpus BLEU** (case-sensitive, `13a` tokenization), plus **chrF2**. Report dataset identifiers, software versions, complete metric signatures, and preprocessing. Estimate paired score differences and bootstrap confidence intervals, preferably resampling whole articles to respect within-document dependence.

**B11**

> 1. **Dataset and metrics:** Use original English source documents and official German references. Freeze systems, exclude training/tuning overlap, and preserve alignment. Report case-sensitive, detokenized **SacreBLEU BLEU**, tokenizer `13a`, plus **chrF2**. Record complete scoring signatures, versions, reference selection, and preprocessing. Report paired score differences with confidence intervals, preferably using document-level bootstrap resampling.

**B17**

> **1. Benchmark and scoring.** Use WMT20’s English-to-German news test set, **newstest2020**. My recollection is that its news was collected in late 2019; verify dates in the official task documentation before use. Do not choose newstest2019 based on “2019.” Use the official English source and German reference files. Score detokenized system outputs with sacreBLEU: case-sensitive corpus BLEU with tokenizer `13a`, plus chrF++ as a secondary measure. Record the full metric signatures, package version, reference selection, and preprocessing.

### F03 — WMT20 findings, Post 2018 and Popović 2015 bibliographic attributions

Status: **supported**. Confirmed error: **no**.

Titles/authors/years and relevance supported; shorthand titles identify real sources.

Sources: [wmt_findings](https://aclanthology.org/2020.wmt-1.1.pdf), [post](https://aclanthology.org/W18-6319/), [chrf](https://aclanthology.org/W15-3049/).

**B01**

> **Confidence and sources.** Confidence is high in the scoring setup, moderate in the temporal fit. A date mismatch or contamination would require another uncontaminated, date-verified sample. Primary sources: the WMT20 news translation task report and Matt Post’s *A Call for Clarity in Reporting BLEU Scores* (2018).

**B04**

> Primary sources: **WMT20 Findings / official news-task release**; **Post (2018), “A Call for Clarity in Reporting BLEU Scores”**; **Popović (2015), “chrF.”** Confidence: high in the scoring setup, moderate in the temporal match. Verified date mismatch or training overlap would change the dataset recommendation.

**B11**

> 4. **Confidence and sources:** High confidence in the scoring approach; moderate confidence in the temporal match. Primary sources: *Findings of WMT 2020*; Post’s *A Call for Clarity in Reporting BLEU Scores* (2018); Popović’s *chrF* paper (2015). A verified date mismatch would change the dataset recommendation.

**B17**

> **4. Confidence and sources.** Confidence is moderate overall; the exact collection dates need checking. Primary sources: *Findings of the 2020 Conference on Machine Translation (WMT20)* and Matt Post’s *A Call for Clarity in Reporting BLEU Scores* (2018). A date mismatch or contamination would require another documented, uncontaminated sample.

### F04 — ImageNet-C scope: 1,000 classes; 15 standard synthetic corruptions; four categories; five severities; CIFAR counterparts

Status: **supported**. Confirmed error: **no**.

Supported. Fifteen is the standard test suite; four additional corruptions exist for further experimentation and do not contradict the standard count.

Sources: [vision_paper](https://arxiv.org/html/1903.12261v1), [vision_repo](https://github.com/hendrycks/robustness).

**B02**

> 1. **Benchmark and metrics.** For 1,000-class ImageNet classification, use ImageNet-C: 15 standard corruptions spanning noise, blur, weather, and digital categories at five severities, plus clean ImageNet validation. Different target labels or imagery make this a proxy. Report clean top-1 error, every corruption/severity’s error, and each corruption’s severity-averaged error. Aggregate mCE is secondary; it cannot establish improvement for every type.

**B06**

> Use ImageNet-C if both classifiers target ImageNet’s 1,000-class object-recognition task. Its 15 standard corruption types span noise, blur, weather, and digital transformations, with five severities per type. Primary source: Hendrycks and Dietterich, *Benchmarking Neural Network Robustness to Common Corruptions and Perturbations* (2019).

**B10**

> For ImageNet-label classifiers, use ImageNet-C: the standard 15 corruption types across noise, blur, weather and digital categories, each at five severities. For CIFAR-label classifiers, use the matching CIFAR-10-C or CIFAR-100-C. Report clean top-1 error, every type-by-severity error, and each type’s error averaged equally across severities. Report mean corruption error (mCE) as a secondary summary; an improved aggregate cannot establish improvement on every type.

**B20**

> 1. Benchmark and metrics. Use ImageNet-C if both classifiers predict ImageNet’s 1,000 classes. Evaluate all 15 standard corruptions at all five severities, using identical images and preprocessing. Report clean top-1 error, each corruption’s error averaged equally across severities, severity-specific errors, and overall mean corruption error. Report the benchmark’s AlexNet-normalized mCE secondarily. Primary source: Hendrycks and Dietterich, *Benchmarking Neural Network Robustness to Common Corruptions and Perturbations* (ICLR 2019).

### F05 — ImageNet-C mCE normalization, severity aggregation, and limits of aggregate corruption metrics

Status: **supported**. Confirmed error: **no**.

Supported: standard mCE averages per-corruption AlexNet-normalized errors over the fifteen types; aggregate improvement need not improve each type. B06 clean/degradation distinction matches Relative mCE motivation.

Qualification: B20 says both overall mean corruption error and AlexNet-normalized mCE; raw average versus normalized quantity should be labeled clearly in implementation, but explicit normalized secondary reporting prevents a direct factual contradiction.

Sources: [vision_paper](https://arxiv.org/html/1903.12261v1), [vision_repo](https://github.com/hendrycks/robustness).

**B02**

> 1. **Benchmark and metrics.** For 1,000-class ImageNet classification, use ImageNet-C: 15 standard corruptions spanning noise, blur, weather, and digital categories at five severities, plus clean ImageNet validation. Different target labels or imagery make this a proxy. Report clean top-1 error, every corruption/severity’s error, and each corruption’s severity-averaged error. Aggregate mCE is secondary; it cannot establish improvement for every type.

**B06**

> 1. **Protocol and metrics.** Freeze models and preprocessing; tune on separate development data. Evaluate identical images and report clean top-1 accuracy, corrupted accuracy at every type/severity, and each type’s equally weighted severity-average error. Report standard mean corruption error (mCE) for comparability, documenting normalization; aggregate mCE cannot establish improvement for every type.

**B10**

> For ImageNet-label classifiers, use ImageNet-C: the standard 15 corruption types across noise, blur, weather and digital categories, each at five severities. For CIFAR-label classifiers, use the matching CIFAR-10-C or CIFAR-100-C. Report clean top-1 error, every type-by-severity error, and each type’s error averaged equally across severities. Report mean corruption error (mCE) as a secondary summary; an improved aggregate cannot establish improvement on every type.

**B20**

> 1. Benchmark and metrics. Use ImageNet-C if both classifiers predict ImageNet’s 1,000 classes. Evaluate all 15 standard corruptions at all five severities, using identical images and preprocessing. Report clean top-1 error, each corruption’s error averaged equally across severities, severity-specific errors, and overall mean corruption error. Report the benchmark’s AlexNet-normalized mCE secondarily. Primary source: Hendrycks and Dietterich, *Benchmarking Neural Network Robustness to Common Corruptions and Perturbations* (ICLR 2019).

### F06 — ImageNet-C Hendrycks/Dietterich paper title and 2019/ICLR attribution

Status: **supported**. Confirmed error: **no**.

Supported by official repository and paper.

Sources: [vision_repo](https://github.com/hendrycks/robustness), [vision_paper](https://arxiv.org/html/1903.12261v1).

**B02**

> 4. **Confidence and sources.** High for ImageNet classifiers; different target imagery or real-weather requirements would change my recommendation. Primary source: Hendrycks and Dietterich, “Benchmarking Neural Network Robustness to Common Corruptions and Perturbations” (2019).

**B06**

> Use ImageNet-C if both classifiers target ImageNet’s 1,000-class object-recognition task. Its 15 standard corruption types span noise, blur, weather, and digital transformations, with five severities per type. Primary source: Hendrycks and Dietterich, *Benchmarking Neural Network Robustness to Common Corruptions and Perturbations* (2019).

**B10**

> My confidence is high in this benchmark choice, conditional on label-space compatibility. Deployment conditions or suspected benchmark exposure would change the recommendation. Primary source: Hendrycks and Dietterich, “Benchmarking Neural Network Robustness to Common Corruptions and Perturbations” (2019).

**B20**

> 1. Benchmark and metrics. Use ImageNet-C if both classifiers predict ImageNet’s 1,000 classes. Evaluate all 15 standard corruptions at all five severities, using identical images and preprocessing. Report clean top-1 error, each corruption’s error averaged equally across severities, severity-specific errors, and overall mean corruption error. Report the benchmark’s AlexNet-normalized mCE secondarily. Primary source: Hendrycks and Dietterich, *Benchmarking Neural Network Robustness to Common Corruptions and Perturbations* (ICLR 2019).

### F07 — HumanEval Python signature/docstring tasks; HumanEval+ expanded tests; MBPP/MBPP+ identity

Status: **supported**. Confirmed error: **no**.

Supported: function-completion identity and stronger test-suite claims match primary sources; MBPP natural-language problem descriptions differ from docstrings.

Sources: [humaneval](https://arxiv.org/abs/2107.03374), [evalplus](https://arxiv.org/abs/2305.01210), [evalplus_repo](https://github.com/evalplus/evalplus/blob/master/README.md), [mbpp](https://arxiv.org/abs/2108.07732).

**B05**

> **Evaluation and metric.** Use HumanEval’s docstring-to-Python tasks, scored with EvalPlus’s stronger HumanEval+ tests. The primary metric should be pass@k at a common candidate budget k; also report pass@1. For n independently sampled completions and c passing completions per task, estimate pass@k as 1 − C(n−c,k)/C(n,k), with n ≥ k, then average across tasks. Primary sources: Chen et al., *Evaluating Large Language Models Trained on Code*; Liu et al., *Is Your Code Generated by ChatGPT Really Correct?*

**B13**

> Use HumanEval: its Python function-completion problems closely match generation from docstrings. Prefer HumanEval+ (EvalPlus) for the primary correctness assessment because its tests catch errors missed by the original tests; also report original HumanEval results for comparability. Add MBPP/MBPP+ as a secondary distribution, acknowledging that its problem statements differ from docstrings.

**B14**

> **Benchmark and metric.** Use HumanEval’s Python docstring-to-function tasks with expanded HumanEval+ tests from EvalPlus. Make **pass@10** primary, fixing the candidate budget at ten; report pass@1 and original-test scores secondarily. Pass@10 measures whether at least one candidate passes, not whether a system can identify it without an oracle.

**B14**

> **Limitations and sufficiency.** Hidden tests approximate correctness; contamination, the small Python-only task set, and decoding sensitivity limit generalization. Add MBPP+ as a secondary replication. This plan suffices for a benchmark-specific comparison, not broad software-engineering superiority.

**B18**

> Use **HumanEval with expanded HumanEval+ tests**, reporting original HumanEval results for comparability. HumanEval matches Python function completion from signatures/docstrings; MBPP provides a secondary distribution check. Scores support claims about these task distributions, not general software-engineering ability.

### F08 — pass@k definition, combinatorial estimator, sufficient n, task average and best-of-k interpretation

Status: **supported**. Confirmed error: **no**.

Estimator and interpretation supported. Oracle phrasing describes whether any candidate succeeds, and correctly distinguishes automatic candidate selection. This is not a claim that the metric evaluates an operational selector.

Sources: [humaneval](https://arxiv.org/abs/2107.03374), [humaneval_code](https://github.com/openai/human-eval/blob/master/human_eval/evaluation.py).

**B05**

> **Evaluation and metric.** Use HumanEval’s docstring-to-Python tasks, scored with EvalPlus’s stronger HumanEval+ tests. The primary metric should be pass@k at a common candidate budget k; also report pass@1. For n independently sampled completions and c passing completions per task, estimate pass@k as 1 − C(n−c,k)/C(n,k), with n ≥ k, then average across tasks. Primary sources: Chen et al., *Evaluating Large Language Models Trained on Code*; Liu et al., *Is Your Code Generated by ChatGPT Really Correct?*

**B13**

> Use pass@k at a preregistered attempt budget k as the primary metric: the fraction of problems with at least one test-passing solution among k samples. Report pass@1 as well. Generate the same n independent completions per problem per model, with n ≥ k, and estimate pass@k using 1 − C(n−c,k)/C(n,k), where c completions pass. This supports choosing the model most likely to solve these benchmark problems within k attempts; it does not establish single-attempt superiority unless k = 1.

**B14**

> **Benchmark and metric.** Use HumanEval’s Python docstring-to-function tasks with expanded HumanEval+ tests from EvalPlus. Make **pass@10** primary, fixing the candidate budget at ten; report pass@1 and original-test scores secondarily. Pass@10 measures whether at least one candidate passes, not whether a system can identify it without an oracle.

**B14**

> **Comparison and decision.** For each model and task, independently generate 100 candidates with identical temperature, top-p, completion-token limits, and stopping rules; publish these settings. Preserve identical task content while documenting necessary model-specific chat formatting. Allow no test feedback, repair, or retries. Estimate each task’s pass@10 as 1 − C(n−c,10)/C(n,10), where n=100 and c is its passing count, then average across tasks. Execute in an isolated sandbox with pinned dependencies, timeouts, tests, and harness. Publish exact model revisions, seeds, prompts, completions, and scoring code. Report paired task-bootstrap confidence intervals for model differences. This supports choosing the model most likely to produce a correct candidate within ten attempts under this protocol.

**B18**

> The primary metric should be **pass@k**, with k fixed in advance to the intended candidate-generation budget. It estimates the probability that at least one of k generated functions passes all tests. Report pass@1 too. Pass@k assumes an oracle can identify a successful candidate; it does not measure the quality of an automatic candidate selector.

**B18**

> Run every model on identical, unmodified prompts and pinned test versions. Generate the same n independent samples per task, with n ≥ k, and use the standard estimator, 1 − C(n−c,k)/C(n,k), where c samples pass. Predeclare decoding settings, stopping rules, token limits, and any equally budgeted tuning. Pin model versions and execution dependencies; publish configurations, seeds, outputs, and evaluation scripts. Execute untrusted code in isolation with fixed resource limits. Report paired task-bootstrap confidence intervals for score differences.

### F09 — HumanEval small Python task scope and finite test coverage; hidden-test phrasing

Status: **supported_with_qualification**. Confirmed error: **no**.

HumanEval has 164 Python tasks; finite tests do not prove full correctness.

Qualification: B14 calls tests hidden. Released benchmark tests are public, but withholding tests from generation is a protocol choice. No assertion of nonpublic secrecy is made; ambiguity is not a confirmed error.

Sources: [humaneval](https://arxiv.org/abs/2107.03374), [evalplus](https://arxiv.org/abs/2305.01210).

**B05**

> **Limitations and sufficiency.** Passing tests is incomplete evidence of correctness; contamination can inflate results. HumanEval is small and does not establish repository-level ability. This plan suffices for a scoped benchmark claim, not broad superiority. Add fresh docstring tasks for stronger generalization evidence.

**B13**

> Limitations include training contamination, finite test coverage, correlated samples, and narrow task scope. This is sufficient for a qualified benchmark comparison, not broad software-engineering claims. Confidence: high for task alignment, moderate for generalization. Fresh held-out docstring tasks or deployment evidence could change the ranking.

**B14**

> **Limitations and sufficiency.** Hidden tests approximate correctness; contamination, the small Python-only task set, and decoding sensitivity limit generalization. Add MBPP+ as a secondary replication. This plan suffices for a benchmark-specific comparison, not broad software-engineering superiority.

**B18**

> Expanded tests reduce false positives but cannot establish complete correctness. Small benchmark size, training contamination, and limited task diversity remain material gaps. This plan suffices for a reproducible benchmark comparison; broader claims require fresh, held-out tasks representative of deployment.

### F10 — HumanEval/EvalPlus/MBPP primary-source authors, titles and years

Status: **supported**. Confirmed error: **no**.

Chen/HumanEval, Liu/EvalPlus, and Austin/MBPP attributions identify real primary papers. Shortened titles are unambiguous.

Sources: [humaneval](https://arxiv.org/abs/2107.03374), [evalplus](https://arxiv.org/abs/2305.01210), [mbpp](https://arxiv.org/abs/2108.07732).

**B05**

> **Evaluation and metric.** Use HumanEval’s docstring-to-Python tasks, scored with EvalPlus’s stronger HumanEval+ tests. The primary metric should be pass@k at a common candidate budget k; also report pass@1. For n independently sampled completions and c passing completions per task, estimate pass@k as 1 − C(n−c,k)/C(n,k), with n ≥ k, then average across tasks. Primary sources: Chen et al., *Evaluating Large Language Models Trained on Code*; Liu et al., *Is Your Code Generated by ChatGPT Really Correct?*

**B13**

> Primary sources: Chen et al. (2021), HumanEval; Liu et al. (2023), EvalPlus; Austin et al. (2021), MBPP.

**B14**

> **Confidence and sources.** High confidence in the design. Different deployment budgets or contamination evidence would change the primary endpoint or require fresh held-out tasks. Primary sources: Chen et al., *Evaluating Large Language Models Trained on Code* (HumanEval/pass@k); Liu et al., *Is Your Code Generated by ChatGPT Really Correct?* (EvalPlus).

**B18**

> Confidence: high for this scope. Known primary sources: Chen et al., *Evaluating Large Language Models Trained on Code* (HumanEval/pass@k); Liu et al.’s EvalPlus work. Deployment-specific requirements could change the benchmark and primary metric.

### F11 — SWE-bench/Verified repository-level issue resolution, percentage resolved, and 2024 release/publication

Status: **supported**. Confirmed error: **no**.

Supported. These resources evaluate automated repository-issue resolution with tests, and do not directly measure human collaboration or active maintainer minutes. Human-time endpoints in the responses are proposed experiments, not claimed standard SWE-bench metrics.

Sources: [swe](https://www.swebench.com/SWE-bench/), [swe_verified](https://openai.com/index/introducing-swe-bench-verified/).

**B12**

> **Tasks and acceptance.** Prefer private or newly collected issues from target repositories. Supplement with SWE-bench Verified, reporting percentage resolved under identical budgets. Require issue-specific hidden tests, regression tests, and blinded reviewer assessment of correctness and maintainability. Primary sources: Jimenez et al., *SWE-bench* (ICLR 2024); OpenAI, *SWE-bench Verified* (2024).

**B12**

> **Limitations and sufficiency.** Public benchmarks risk contamination; historical issues and recruited maintainers may poorly represent deployment. Review judgments introduce uncertainty. SWE-bench alone cannot demonstrate time savings; the human study is sufficient for the sampled workflows, with replication needed for broader claims. Confidence is high in this design, moderate in dataset relevance. Different users, workflows, or high failure rates would change sampling, budgets, and power requirements.

**B19**

> 1. **Evaluation and metrics.** Randomize issues between the candidate and current assistant within maintainer and repository, blocking by estimated difficulty. Each issue is attempted once. Use representative issues. Primary metric: **total active maintainer minutes per accepted fix**, calculated as all development, review, and rework minutes divided by accepted fixes in each arm. Include effort spent on failures. Prespecify abandonment rules and an acceptance-rate noninferiority requirement. Report elapsed completion time separately. Use SWE-bench Verified as a secondary correctness screen, reporting resolved percentage under identical tool and compute budgets.

**B19**

> 3. **Limitations.** Contamination, benchmark selection, generated-test weaknesses, learning effects, and repository familiarity limit inference. SWE-bench alone is insufficient; representative field evidence is necessary. Generalization beyond sampled maintainers remains qualified.

**B19**

> 4. **Confidence and sources.** High confidence in the design; sample size needs pilot variance estimates. Primary sources: the SWE-bench paper and dataset; METR’s 2025 randomized study of experienced open-source developers. Different target workflows or carryover would change the trial design.

**B21**

> 3. **Supporting evidence and limitations.** SWE-bench and SWE-bench Verified provide Python repository issue tasks; report resolved percentage as a secondary capability check. They omit human collaboration and may suffer contamination or unrepresentative task selection. The field study supports the claim only for sampled maintainers, tasks, and configurations.

**B21**

> 4. **Confidence and sources.** High confidence in this design; recruitment or instrumentation constraints could require a narrower claim. Primary sources: the SWE-bench paper and METR’s “Measuring the Impact of Early-2025 AI on Experienced Open-Source Developer Productivity.”

**B22**

> Use SWE-bench or SWE-bench Verified as an auxiliary repository-level capability screen; report resolved percentage under identical agent scaffolding and compute budgets. Primary sources include Jimenez et al., “SWE-bench: Can Language Models Resolve Real-World GitHub Issues?” and OpenAI’s SWE-bench Verified release. These measure automated issue resolution, not maintainer time savings; historical-task contamination and benchmark representativeness limit inference.

### F12 — METR 2025 randomized experienced open-source developer study identity

Status: **supported**. Confirmed error: **no**.

Supported study identity/year and randomized-developer description. Neither response claims a numeric slowdown or speedup or attributes its custom time endpoint to METR.

Sources: [metr](https://metr.org/blog/2025-07-10-early-2025-ai-experienced-os-dev-study/).

**B19**

> 4. **Confidence and sources.** High confidence in the design; sample size needs pilot variance estimates. Primary sources: the SWE-bench paper and dataset; METR’s 2025 randomized study of experienced open-source developers. Different target workflows or carryover would change the trial design.

**B21**

> 4. **Confidence and sources.** High confidence in this design; recruitment or instrumentation constraints could require a narrower claim. Primary sources: the SWE-bench paper and METR’s “Measuring the Impact of Early-2025 AI on Experienced Open-Source Developer Productivity.”

### F13 — MATH competition problems, test set, topic/difficulty structure, worked references and 2021 attribution

Status: **supported**. Confirmed error: **no**.

Supported dataset properties and bibliography. The supplied worked solutions can guide graders; the proposed rubric and exact population fit are methodological choices, not documented benchmark guarantees.

Sources: [math](https://arxiv.org/html/2103.03874v2).

**B03**

> **1. Resources and metrics.** Use a prespecified, stratified sample from the held-out MATH benchmark (Hendrycks et al., *Measuring Mathematical Problem Solving With the MATH Dataset*, 2021), restricted to problems matching your high-school competition scope. Its reference solutions support review; final-answer accuracy alone does not measure logical correctness. Use PRM800K (Lightman et al., *Let’s Verify Step by Step*, 2023) to develop and calibrate a step-correctness rubric, not as a replacement for judging your assistants’ outputs.

**B07**

> Use **MATH** (Hendrycks et al., *Measuring Mathematical Problem Solving*) for problems, selecting a held-out subset representative of the intended high-school competition levels and topics. Its answer accuracy alone cannot establish logical correctness. Use **PRM800K** (Lightman et al., *Let’s Verify Step by Step*) as a source of human step-level judgments to develop an annotation rubric; its existing solutions do not directly compare your assistants.

**B09**

> 1. **Resource and metrics.** Use the public MATH test set (Hendrycks et al., *Measuring Mathematical Problem Solving With the MATH Dataset*, 2021), stratified by subject and difficulty. Its competition mathematics and reference solutions fit the task reasonably well. Primary metric: fraction of complete solutions judged mathematically valid, with justified inferences and a supported conclusion. Report final-answer accuracy separately: a correct answer can accompany invalid reasoning.

**B09**

> 3. **Conclusions and sufficiency.** This supports “more logically correct written solutions on the evaluated MATH distribution under these settings.” Answer accuracy alone, or an unvalidated automated judge, is insufficient. Expert process assessment is sufficient for that restricted claim, but public-data contamination and benchmark selection limit broader claims about unseen high-school competitions. Add freshly authored or securely held-out contest-style problems for that inference, and disclose possible training overlap.

**B23**

> Use a prespecified sample of the public MATH test set, stratified by topic and difficulty (Hendrycks et al., *Measuring Mathematical Problem Solving With the MATH Dataset*, 2021). Generate paired worked solutions under matched prompting and sampling conditions. Published solutions should guide grading without excluding alternative valid arguments. Two mathematically qualified graders should independently assess anonymized, randomly ordered outputs, then adjudicate disagreements.

**B23**

> MATH is primarily answer-oriented, and public-test contamination, grader fallibility, and limited coverage of proof competitions constrain generalization. This plan is sufficient for the narrowed claim, not universal mathematical reliability. My confidence is high in the scoring approach and moderate in benchmark representativeness. Evidence of training overlap, a focus on olympiad proofs, or deployment-specific problem distributions would favor additional fresh, independently authored problems and proof-focused evaluation.

### F14 — MATH standard final-answer scoring versus logical/process correctness

Status: **supported**. Confirmed error: **no**.

Supported by answer-equivalence standard scoring and the paper’s explicit correct-answer/wrong-explanation example. Primarily answer-oriented is read as standard scoring, consistent with reference solutions also existing.

Qualification: Limited fit to proof competitions is a scope inference, not an independently established exhaustive survey of competition populations.

Sources: [math](https://arxiv.org/html/2103.03874v2).

**B03**

> **1. Resources and metrics.** Use a prespecified, stratified sample from the held-out MATH benchmark (Hendrycks et al., *Measuring Mathematical Problem Solving With the MATH Dataset*, 2021), restricted to problems matching your high-school competition scope. Its reference solutions support review; final-answer accuracy alone does not measure logical correctness. Use PRM800K (Lightman et al., *Let’s Verify Step by Step*, 2023) to develop and calibrate a step-correctness rubric, not as a replacement for judging your assistants’ outputs.

**B03**

> **2. Scoring and decision.** Generate one solution per assistant per problem under matched settings. Have two qualified reviewers independently score anonymized, randomly ordered solutions, then adjudicate disagreements. Define the primary outcome as a complete, logically valid solution: correct conclusion, justified essential steps, and no substantive gaps or invalid inferences. Accept alternative valid methods. Report each assistant’s success rate, the paired difference with a 95% confidence interval, reviewer agreement before adjudication, and secondary final-answer accuracy. Prespecify sample size and a practically meaningful improvement. A sufficiently precise positive paired difference supports greater logical correctness on the evaluated problem distribution.

**B07**

> Use **MATH** (Hendrycks et al., *Measuring Mathematical Problem Solving*) for problems, selecting a held-out subset representative of the intended high-school competition levels and topics. Its answer accuracy alone cannot establish logical correctness. Use **PRM800K** (Lightman et al., *Let’s Verify Step by Step*) as a source of human step-level judgments to develop an annotation rubric; its existing solutions do not directly compare your assistants.

**B07**

> Generate both assistants’ worked solutions to the same problems under matched, preregistered prompting and sampling conditions. Have mathematically qualified raters, blinded to assistant identity, independently assess each complete solution. Define the primary metric as the proportion with no substantive false inference, unsupported essential step, or material reasoning gap. Specify permissible routine omissions. Adjudicate disagreements and report agreement. Report final-answer accuracy and error categories separately. Estimate the paired difference in fully valid solution rates with a confidence interval, clustering by problem if sampling multiple solutions.

**B09**

> 1. **Resource and metrics.** Use the public MATH test set (Hendrycks et al., *Measuring Mathematical Problem Solving With the MATH Dataset*, 2021), stratified by subject and difficulty. Its competition mathematics and reference solutions fit the task reasonably well. Primary metric: fraction of complete solutions judged mathematically valid, with justified inferences and a supported conclusion. Report final-answer accuracy separately: a correct answer can accompany invalid reasoning.

**B09**

> 3. **Conclusions and sufficiency.** This supports “more logically correct written solutions on the evaluated MATH distribution under these settings.” Answer accuracy alone, or an unvalidated automated judge, is insufficient. Expert process assessment is sufficient for that restricted claim, but public-data contamination and benchmark selection limit broader claims about unseen high-school competitions. Add freshly authored or securely held-out contest-style problems for that inference, and disclose possible training overlap.

**B23**

> The primary metric should be the proportion of complete, logically correct solutions. Publish a rubric covering invalid inferences, substantive gaps, arithmetic errors, and incomplete attempts. Report final-answer accuracy separately, alongside error categories and pre-adjudication agreement. Estimate the paired improvement with a problem-level bootstrap confidence interval. Preregister sample size and a meaningful improvement threshold; declare substantive superiority only if the interval’s lower bound exceeds that threshold.

**B23**

> This supports the claim that the new assistant produces more logically correct written solutions on the represented competition problems under the tested conditions. It supports choosing that assistant for this setting, provided the improvement is practically meaningful. Answer accuracy alone cannot establish the paper’s claim.

**B23**

> MATH is primarily answer-oriented, and public-test contamination, grader fallibility, and limited coverage of proof competitions constrain generalization. This plan is sufficient for the narrowed claim, not universal mathematical reliability. My confidence is high in the scoring approach and moderate in benchmark representativeness. Evidence of training overlap, a focus on olympiad proofs, or deployment-specific problem distributions would favor additional fresh, independently authored problems and proof-focused evaluation.

### F15 — PRM800K human step labels, fixed model-generated traces, and Lightman 2023 source

Status: **supported**. Confirmed error: **no**.

Supported: PRM800K contains human labels on generated MATH steps; fixed traces cannot directly compare newly generated outputs from two unspecified assistants. Rubric development/calibration is a proposed use.

Sources: [prm](https://github.com/openai/prm800k), [prm_paper](https://arxiv.org/abs/2305.20050).

**B03**

> **1. Resources and metrics.** Use a prespecified, stratified sample from the held-out MATH benchmark (Hendrycks et al., *Measuring Mathematical Problem Solving With the MATH Dataset*, 2021), restricted to problems matching your high-school competition scope. Its reference solutions support review; final-answer accuracy alone does not measure logical correctness. Use PRM800K (Lightman et al., *Let’s Verify Step by Step*, 2023) to develop and calibrate a step-correctness rubric, not as a replacement for judging your assistants’ outputs.

**B07**

> Use **MATH** (Hendrycks et al., *Measuring Mathematical Problem Solving*) for problems, selecting a held-out subset representative of the intended high-school competition levels and topics. Its answer accuracy alone cannot establish logical correctness. Use **PRM800K** (Lightman et al., *Let’s Verify Step by Step*) as a source of human step-level judgments to develop an annotation rubric; its existing solutions do not directly compare your assistants.

**B07**

> Material limitations include benchmark contamination, imperfect representativeness, rater error, and PRM800K’s different solution distribution. The plan is sufficient for a qualified benchmark claim; broader claims require fresh competition-style problems and broader sampling.

### F16 — PRM800K differs from the evaluated assistants’ solution distribution

Status: **unresolved**. Confirmed error: **no**.

PRM800K’s generation provenance is established, but actual compared assistant distributions are unspecified. A difference is plausible, not directly verified.

Qualification: This is not directly contradicted. Treat as a transfer-risk caveat rather than proof of actual measured distribution shift.

Sources: [prm](https://github.com/openai/prm800k).

**B07**

> Material limitations include benchmark contamination, imperfect representativeness, rater error, and PRM800K’s different solution distribution. The plan is sufficient for a qualified benchmark claim; broader claims require fresh competition-style problems and broader sampling.

### F17 — ALCE bibliographic identity, citation-evaluation methods, and general-domain task scope

Status: **supported**. Confirmed error: **no**.

Supported. ALCE’s original citation recall/precision use statement-level entailment and citation relevance on general-domain tasks; those tasks alone cannot establish physics-review performance.

Sources: [alce](https://aclanthology.org/2023.emnlp-main.398.pdf).

**B08**

> 1. **Benchmark.** Build a held-out set of representative physics literature-review requests, stratified by subfield, recency, and synthesis difficulty. Use full papers as evidence. ALCE (*Enabling Large Language Models to Generate Text with Citations*, Gao et al., 2023) provides citation-evaluation concepts; its general-domain tasks cannot establish physics-review performance.

**B15**

> Benchmarks and metrics. Build held-out physics review requests spanning subfields, dates, and contentious claims. Adapt ALCE (Gao et al., “Enabling Large Language Models to Generate Text with Citations,” 2023) for attribution scoring; its datasets alone do not establish physics performance. Primary metric: the fraction of citation–claim pairs whose reference is real, correctly identified, and supports the attached claim. Also report fabricated-reference rate and citation completeness.

**B16**

> 1. **Benchmark and metrics.** Build held-out physics-review prompts sampled from intended users’ work, stratified by subfield, topic age, and difficulty. ALCE (Gao et al., 2023, *Enabling Large Language Models to Generate Text with Citations*) offers useful methodology, but its tasks do not establish physics-review performance. Measure **fabricated-reference rate** per bibliography entry and **unsupported-citation rate** per atomic claim–citation link; nonexistent references fail support too. Separately measure metadata errors, support coverage across all verifiable claims, and scientific correctness, preventing improvement through omitted claims or citations.

**B24**

> **Limitations and sufficiency.** ALCE (Gao et al., “Enabling Large Language Models to Generate Text with Citations,” 2023) provides citation-evaluation methodology; SciFact (Wadden et al., 2020) provides scientific claim–evidence examples. Neither establishes physics-review performance. Validate automated entailment judges against expert annotations. Track completeness to detect gains obtained by omitting difficult claims or citations. This plan is sufficient for conclusions about the sampled topics and accessible sources, not physics literature generally.

### F18 — Proposed citation metrics are custom adaptations, not asserted original ALCE formulas

Status: **methodological_not_historical_fact**. Confirmed error: **no**.

Responses define their own atomic-claim/link and existence/support metrics. None asserts exact identity with original ALCE metrics; differences from ALCE are not factual errors.

Sources: [alce](https://aclanthology.org/2023.emnlp-main.398.pdf).

**B08**

> 2. **Primary metric and claim.** Use **supported-claim coverage**: the fraction of externally checkable atomic scientific claims supported by correctly identified, existing cited papers. Uncited claims, fabricated references, and unsupported citations count as failures. Separately measure fabricated-reference rate per unique reference and citation-support precision. Higher coverage establishes better documented support; demonstrating “fewer invented references” additionally requires lower fabrication rates. Predefine both success criteria and multiplicity handling.

**B15**

> Benchmarks and metrics. Build held-out physics review requests spanning subfields, dates, and contentious claims. Adapt ALCE (Gao et al., “Enabling Large Language Models to Generate Text with Citations,” 2023) for attribution scoring; its datasets alone do not establish physics performance. Primary metric: the fraction of citation–claim pairs whose reference is real, correctly identified, and supports the attached claim. Also report fabricated-reference rate and citation completeness.

**B16**

> 1. **Benchmark and metrics.** Build held-out physics-review prompts sampled from intended users’ work, stratified by subfield, topic age, and difficulty. ALCE (Gao et al., 2023, *Enabling Large Language Models to Generate Text with Citations*) offers useful methodology, but its tasks do not establish physics-review performance. Measure **fabricated-reference rate** per bibliography entry and **unsupported-citation rate** per atomic claim–citation link; nonexistent references fail support too. Separately measure metadata errors, support coverage across all verifiable claims, and scientific correctness, preventing improvement through omitted claims or citations.

**B24**

> **Benchmark and metrics.** Build held-out physics review prompts, stratified by subfield and publication cutoff. Annotate atomic scientific claims and claim–reference links. Primary metric: **valid-and-supporting citation precision**, the fraction of links whose reference exists, is correctly identified, and supports the associated claim. Also report fabricated-reference rate per unique reference, citation completeness, and scientific accuracy. Average scores across prompts.

### F19 — SciFact scientific claim–evidence examples and Wadden 2020 attribution

Status: **supported**. Confirmed error: **no**.

Supported: scientific claims with evidence-containing abstracts; no claim that SciFact directly measures complete physics-review performance.

Sources: [scifact](https://aclanthology.org/2020.emnlp-main.609/).

**B24**

> **Limitations and sufficiency.** ALCE (Gao et al., “Enabling Large Language Models to Generate Text with Citations,” 2023) provides citation-evaluation methodology; SciFact (Wadden et al., 2020) provides scientific claim–evidence examples. Neither establishes physics-review performance. Validate automated entailment judges against expert annotations. Track completeness to detect gains obtained by omitting difficult claims or citations. This plan is sufficient for conclusions about the sampled topics and accessible sources, not physics literature generally.

## Primary source evidence

- **wmt_task** — [https://www.statmt.org/wmt20/translation-task.html](https://www.statmt.org/wmt20/translation-task.html). DATA, lines 98; Document-level MT, lines 47–49. Official page specifies online newspapers from September–November 2019, original source text and human target translations; English↔German uses paragraph segments.
- **wmt_findings** — [https://aclanthology.org/2020.wmt-1.1.pdf](https://aclanthology.org/2020.wmt-1.1.pdf). §2.1, Table 1. Official 2020 findings identify public news benchmarks and source-original/paragraph-segmented English→German data, with alternative German references.
- **sacrebleu** — [https://github.com/mjpost/sacrebleu](https://github.com/mjpost/sacrebleu). Features; scoring; multiple metrics; version signatures. Official README documents detokenized scoring, case-sensitive BLEU/13a, chrF2, chrF++ with word order 2, complete signatures, multi-reference scoring and paired bootstrap support.
- **sacre_datasets** — [https://github.com/mjpost/sacrebleu/blob/master/DATASETS.md](https://github.com/mjpost/sacrebleu/blob/master/DATASETS.md). wmt20 entry, retrieved search result. Official dataset registry names wmt20 as the official WMT20 evaluation dataset. Direct dataset implementation retrieval failed; the precise en-de file mapping was not executed locally.
- **post** — [https://aclanthology.org/W18-6319/](https://aclanthology.org/W18-6319/). Abstract and bibliographic metadata. Matt Post, 2018, A Call for Clarity in Reporting BLEU Scores. Explains parameter/reference-processing effects on BLEU comparability and introduces SacreBLEU.
- **chrf** — [https://aclanthology.org/W15-3049/](https://aclanthology.org/W15-3049/). Bibliographic metadata. Maja Popović, 2015, chrF: character n-gram F-score for automatic MT evaluation.
- **vision_paper** — [https://arxiv.org/html/1903.12261v1](https://arxiv.org/html/1903.12261v1). §4.1–4.2, Fig.1, CE/mCE equations; §5.1. Defines 15 standard corruption types in four categories at five severities on ImageNet validation images. CE sums error over severities and normalizes by AlexNet; mCE averages 15 CEs. Relative mCE separates degradation from corrupted accuracy.
- **vision_repo** — [https://github.com/hendrycks/robustness](https://github.com/hendrycks/robustness). ImageNet-C; leaderboard discussion; Calculating mCE. Official repository confirms 1,000 classes, CIFAR-10-C/CIFAR-100-C, ICLR 2019 attribution and per-corruption tradeoffs; some methods improve some corruptions and hurt others.
- **humaneval** — [https://arxiv.org/abs/2107.03374](https://arxiv.org/abs/2107.03374). Primary HumanEval paper. Chen et al., 2021, Evaluating Large Language Models Trained on Code; 164 Python function-completion tasks with signatures/docstrings and functional-correctness evaluation.
- **humaneval_code** — [https://github.com/openai/human-eval/blob/master/human_eval/evaluation.py](https://github.com/openai/human-eval/blob/master/human_eval/evaluation.py). estimate_pass_at_k and evaluate_functional_correctness. Official evaluator implements 1−C(n−c,k)/C(n,k), uses only k with sufficient n, and averages task estimates.
- **evalplus** — [https://arxiv.org/abs/2305.01210](https://arxiv.org/abs/2305.01210). Primary EvalPlus paper. Liu et al., 2023, Is Your Code Generated by ChatGPT Really Correct? Stronger HumanEval+ tests expose errors missed by original tests.
- **evalplus_repo** — [https://github.com/evalplus/evalplus/blob/master/README.md](https://github.com/evalplus/evalplus/blob/master/README.md). HumanEval+ and MBPP+ documentation. Official project supplies expanded HumanEval+ and MBPP+ test suites.
- **mbpp** — [https://arxiv.org/abs/2108.07732](https://arxiv.org/abs/2108.07732). Austin et al., 2021 primary MBPP paper. MBPP consists of short Python programming tasks described in natural language; its prompt format differs from HumanEval function docstrings.
- **swe** — [https://www.swebench.com/SWE-bench/](https://www.swebench.com/SWE-bench/). Official SWE-bench documentation and publication. Jimenez et al., SWE-bench: Can Language Models Resolve Real-World GitHub Issues?, ICLR 2024, evaluates patches for real GitHub issues in Python repositories through test-based resolution.
- **swe_verified** — [https://openai.com/index/introducing-swe-bench-verified/](https://openai.com/index/introducing-swe-bench-verified/). Official 2024 release. SWE-bench Verified is a human-validated subset for automated repository issue resolution, not a measure of maintainer labor.
- **metr** — [https://metr.org/blog/2025-07-10-early-2025-ai-experienced-os-dev-study/](https://metr.org/blog/2025-07-10-early-2025-ai-experienced-os-dev-study/). METR primary randomized study report, July 10 2025. Measuring the Impact of Early-2025 AI on Experienced Open-Source Developer Productivity reports a randomized study with experienced open-source developers working in familiar repositories.
- **math** — [https://arxiv.org/html/2103.03874v2](https://arxiv.org/html/2103.03874v2). §3.1–3.2, Fig.3. Hendrycks et al., 2021, MATH has competition problems, public train/test split, seven subjects, five difficulties, worked reference solutions and boxed answers. Standard scoring compares final answers; Fig.3 illustrates correct answer with wrong explanation.
- **prm** — [https://github.com/openai/prm800k](https://github.com/openai/prm800k). README introduction and labeling instructions. PRM800K releases human step-correctness labels for model-generated MATH solutions, plus labeling instructions.
- **prm_paper** — [https://arxiv.org/abs/2305.20050](https://arxiv.org/abs/2305.20050). Primary paper metadata/abstract. Lightman et al., Let’s Verify Step by Step, 2023, distinguishes process supervision from outcome supervision and releases process labels.
- **alce** — [https://aclanthology.org/2023.emnlp-main.398.pdf](https://aclanthology.org/2023.emnlp-main.398.pdf). Table 1, §2 and §3.3. Gao et al., 2023, ALCE uses ASQA/QAMPARI with Wikipedia and ELI5 with Sphere. Citation recall checks statement support by concatenated cited passages; precision checks citation relevance using entailment. These differ from the proposed custom atomic-claim/link metrics.
- **scifact** — [https://aclanthology.org/2020.emnlp-main.609/](https://aclanthology.org/2020.emnlp-main.609/). Abstract and bibliographic metadata. Wadden et al., 2020, SciFact supplies expert scientific claims paired with evidence-containing abstracts and annotations.
