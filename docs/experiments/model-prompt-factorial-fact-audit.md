# Bounded fact audit

All 24 responses read, all six case families covered. Repeated assertions grouped. This is bounded coverage, not exhaustive proof that every assertion is true. Pure proposed methods and primary recommendation quality are not rated.

No model/form manifest, key, ratings, history, or other local study input inspected.

## Result

One repeated temporal-provenance error was confirmed, affecting F01 and F18: the WMT19 organizers specify September–November 2018 articles, whereas WMT20 specifies September–November 2019. F17’s claim is supported. F21’s qualified recollection is also supported. No additional direct primary contradiction was established. This is not a recommendation rating.

## Coverage

| Family | Responses | External facts checked |
|---|---|---|
| Translation | F01, F17, F18, F21 | WMT identity/provenance; BLEU, chrF, COMET; source names/years |
| Functions | F04, F08, F16, F24 | HumanEval, MBPP, EvalPlus identities; pass@k scope/formula; sampling precedent |
| Vision | F03, F06, F12, F20 | ImageNet-C design, paper identity/year, mCE normalization |
| Math | F07, F11, F19, F22 | MATH identity, labels/solutions/split, answer metric versus written correctness |
| Maintainer | F05, F10, F13, F23 | SWE-bench/Verified identity and measured scope; F13/F23 are custom study proposals |
| Physics | F02, F09, F14, F15 | ALCE, FActScore, SciFact identities/scope/year; F09/F14 are custom audit proposals |

## Grouped claim record

### MT-DATE-W19 — confirmed_error

WMT19/newstest2019 matches news from late 2019.

Direct contradiction: official planned article window is September–November 2018. The response passages assert a late-2019 temporal fit. This is one repeated factual error affecting two responses, not two independent benchmark identities.

**F01 exact passage:**

> 1. **Benchmark and scoring.** Use WMT 2019 English→German news translation test set, commonly called **newstest2019**. It is public, held-out online-news text from late 2019 and directly matches the requested domain and period. Score both systems against the same official references with **SacreBLEU** (case-sensitive, standard 13a tokenization; report the full SacreBLEU signature) and a modern reference-based metric such as **COMET**, naming the exact model/checkpoint. Add paired bootstrap resampling over sentences for uncertainty in the system difference. Do not tune on this test set.

**F18 exact passage:**

> Use the WMT 2019 English→German news translation test set, usually called `newstest2019` (also distributed in the WMT19 test data). It consists of held-out news material from the 2019 evaluation campaign and is the closest standard public benchmark for online news from late 2019. Keep the official source and reference files together and do not tune or select checkpoints against this set; if either system has already used it for development, the comparison is no longer fully held out.

Evidence: [wmt19](https://www.statmt.org/wmt19/translation-task.html) — Test data, line 104 of retrieved text. The organizers specify September–November 2018 online newspapers for the 2019 test sets; English↔German is an established pair.

### MT-DATE-W20 — supported

WMT20/newstest2020 corresponds to late-2019 news.

F21 explicitly expresses uncertainty and requires verification; the retrieved primary documentation supports its recollection. The WMT20 page describes the planned source window, not a per-document realized-date audit.

**F17 exact passage:**

> Use **WMT20 News Translation’s English→German test set, `newstest2020`**. Its news material was collected in late 2019; the benchmark name reflects the 2020 shared task. That distinction matters when choosing a test set by the dates of the underlying articles.

**F21 exact passage:**

> I recommend WMT20’s English→German news test set, `newstest2020`, with its official source and human references. My recollection is that its news was collected in late 2019; I am not certain of the exact collection window, so confirm that provenance in the release documentation before asserting the temporal match. Preserve document boundaries and use English-original material. Keep this set out of training, tuning, and system selection.

Evidence: [wmt20](https://www.statmt.org/wmt20/translation-task.html) — Test data, line 98 of retrieved text. The organizers specify September–November 2019 online newspapers for the 2020 test sets, with original source text and human target translations.; [wmt20_report](https://aclanthology.org/2020.wmt-1.1.pdf) — Section 2.1, pp.2–3. The report describes released news test sets and source-original directionality; English↔German uses paragraph-split source texts for translation.

### MT-SCORE — supported

SacreBLEU case-sensitive 13a, signatures and detokenized input; chrF/chrF2 as character-based complement.

BLEU is a conventional automatic score, not the WMT official human-quality outcome; these responses propose an evaluation and do not falsely assert otherwise. The exact commands were checked against documented CLI shape, not executed against current downloads.

**F01 exact passage:**

> 1. **Benchmark and scoring.** Use WMT 2019 English→German news translation test set, commonly called **newstest2019**. It is public, held-out online-news text from late 2019 and directly matches the requested domain and period. Score both systems against the same official references with **SacreBLEU** (case-sensitive, standard 13a tokenization; report the full SacreBLEU signature) and a modern reference-based metric such as **COMET**, naming the exact model/checkpoint. Add paired bootstrap resampling over sentences for uncertainty in the system difference. Do not tune on this test set.

**F17 exact passage:**

> Supply detokenized predictions. The standard BLEU setup uses the `13a` tokenizer; let SacreBLEU apply it consistently. Report BLEU as the primary conventional score and chrF as a complementary character-based measure. Record the SacreBLEU version and complete metric signatures, including the reference count, tokenization, and case settings. If using additional or alternative references, identify that configuration explicitly.

**F18 exact passage:**

> For a reproducible primary score, report corpus BLEU with SacreBLEU against the official reference, using its standard `13a` tokenizer and case-sensitive (“mixed case”) scoring. Include the complete SacreBLEU signature in the report (and the SacreBLEU version), so tokenization, normalization, and reference choices are explicit. Score both systems on exactly the same sentence set and reference. Do not compare a score produced with a different tokenizer or BLEU implementation as though it were directly equivalent.

**F21 exact passage:**

> Score both systems on identical segments using SacreBLEU corpus BLEU, case-sensitive, with the standard `13a` tokenizer, plus chrF2 as a complementary character-based metric. Supply detokenized German output and record the SacreBLEU version, full signatures, reference configuration, and preprocessing. Report score differences and paired bootstrap confidence intervals; resample documents when document boundaries are available. A higher score with a consistently positive difference supports choosing that system for this particular news benchmark.

Evidence: [sacrebleu](https://github.com/mjpost/sacrebleu) — README: default tokenization, metric signatures, multiple metrics. Documentation specifies 13a for non-CJK defaults, case sensitivity by default, detokenized input, signatures, chrF2 default and BLEU/chrF CLI selection.; [post](https://aclanthology.org/W18-6319/) — Paper metadata/abstract. Matt Post, A Call for Clarity in Reporting BLEU Scores, 2018.; [chrf](https://aclanthology.org/W15-3049/) — Paper metadata/abstract. Maja Popović, chrF: character n-gram F-score for automatic MT evaluation, 2015.

### MT-COMET — supported

COMET can supply a modern reference-based additional MT metric.

No exact checkpoint or score is asserted. Model choice is a proposal, not an empirical fact to certify.

**F01 exact passage:**

> 1. **Benchmark and scoring.** Use WMT 2019 English→German news translation test set, commonly called **newstest2019**. It is public, held-out online-news text from late 2019 and directly matches the requested domain and period. Score both systems against the same official references with **SacreBLEU** (case-sensitive, standard 13a tokenization; report the full SacreBLEU signature) and a modern reference-based metric such as **COMET**, naming the exact model/checkpoint. Add paired bootstrap resampling over sentences for uncertainty in the system difference. Do not tune on this test set.

**F18 exact passage:**

> BLEU alone can miss meaningful adequacy and fluency differences. If you want a complementary metric, compute a current COMET model score on the same source, hypotheses, and reference, and label its model/version. Treat that as an additional metric rather than mixing it with BLEU. For a stronger claim about which system performs better, use paired bootstrap resampling over sentences and report the score difference with uncertainty; a small BLEU gap may not be statistically meaningful.
> 

Evidence: [comet](https://aclanthology.org/2020.emnlp-main.213/) — Paper abstract. COMET is a neural MT-evaluation framework. A reference-based configuration uses source, hypothesis and reference; checkpoint choice matters.

### FUNCTION-ID — supported

HumanEval is Python function completion from signatures/docstrings with executable behavior tests.

F24 calls the unit tests hidden. They are withheld from the completion prompt but publicly released; read as permanently secret, that word would be misleading. Marked qualification rather than confirmed substantive contradiction because prompt-hidden is a standard evaluation meaning.

**F04 exact passage:**

> Use **HumanEval**, a benchmark of Python function-completion tasks with signatures, docstrings, and executable tests. Prefer the expanded **HumanEval+** tests for stronger correctness checks, recording the exact version. Evaluate every model yourself against the same suite; published scores using different tests or settings are not directly comparable.

**F08 exact passage:**

> **Benchmark and metric.** Use HumanEval for docstring-to-standalone-Python generation, with the expanded HumanEval+ tests from EvalPlus. Make pass@k at a preregistered, shared generation budget k the primary metric: the fraction of tasks for which at least one of k candidates passes every test. Report pass@1 alongside it. Use MBPP as a secondary generalization check, keeping its results separate.

**F16 exact passage:**

> **(1) Evaluation and metric.** Use HumanEval and MBPP as standard function-from-description benchmarks, evaluated with EvalPlus’s HumanEval+ and MBPP+ expanded tests. Make pass@1 the primary metric: the proportion of problems for which one sampled completion passes all tests. Report pass@k (for a prespecified k within the shared generation budget) as secondary, using the standard unbiased estimator when estimating it from multiple samples. The primary sources are Chen et al., “Evaluating Large Language Models Trained on Code” (HumanEval), Austin et al., “Program Synthesis with Large Language Models” (MBPP), and Liu et al., “Is Your Code Generated by ChatGPT Really Correct? Rigorous Evaluation of Large Language Models for Code Generation” (EvalPlus).

**F24 exact passage:**

> Use **HumanEval** with **pass@k** as the primary metric. Its tasks ask a model to implement a standalone Python function from a prompt and docstring, and hidden unit tests check functional behavior. Report pass@1 as the headline measure of single-sample correctness; include pass@10 if the intended use permits multiple attempts. Use the benchmark’s canonical tasks and tests, and state any exclusions or test-harness changes.

Evidence: [humaneval](https://arxiv.org/pdf/2107.03374) — Section 2, pp.2–3; arXiv metadata. Chen et al. 2021 introduces Python docstring function completion and test-based functional correctness. The paper uses n=200, n≥k, and the stated combinatorial unbiased pass@k estimator averaged over problems.; [humanrepo](https://github.com/openai/human-eval) — README, Usage example. Official repository releases evaluation data/code and demonstrates 200 samples per task; tests are public, although they are withheld from the generation prompt.

### FUNCTION-METRIC — supported

pass@k and its combinatorial estimator, including pass@1 and 200-sample precedent.

Pass@k concerns at least one test-passing sample under specified sampling. 200 is a paper/repository precedent and the answer says typically, not a mathematical requirement. Fixed candidate budget is not necessarily fixed compute; F08 explicitly distinguishes them.

**F04 exact passage:**

> The primary metric should be **pass@k**, with **k fixed in advance to the shared sampling budget**: the probability that at least one of k candidates passes all tests for a task. For one attempt, this is pass@1. Report pass@1 alongside larger-budget results.

**F04 exact passage:**

> - Give models identical task information, adapting only necessary interface formatting. Freeze model versions and exclude benchmark examples from tuning.
> - Generate the same number n of independent candidates per task, with n ≥ k. Record prompts, seeds, temperature, top-p, token limits, stopping rules, and postprocessing. Fix decoding settings beforehand or allow equal development-set tuning budgets.
> - Execute candidates in an isolated sandbox with identical Python dependencies, timeouts, and resource limits. Syntax errors, exceptions, timeouts, and failed assertions count as failures. Never select candidates using evaluation tests.
> - If c of n candidates pass, estimate task-level pass@k as 1 − C(n−c,k)/C(n,k), then average equally across tasks. Report paired confidence intervals across tasks, configuration details, and per-task outcomes.

**F08 exact passage:**

> **Comparison and decision.** Freeze benchmark versions, prompts, model checkpoints, decoding settings, completion limits, seeds, and execution environments. Use identical task inputs and candidate counts; publish necessary model-specific formatting. Generate n independent candidates per task, with n ≥ k, and estimate pass@k using 1 − C(n−c,k)/C(n,k), where c candidates pass. Execute in an isolated sandbox with fixed timeouts. Report paired, task-level bootstrap confidence intervals and decoding sensitivity. This supports choosing the model more likely to produce a test-passing candidate under that sampling budget. Equal candidate counts do not imply equal compute or token costs; report those separately.

**F16 exact passage:**

> **(1) Evaluation and metric.** Use HumanEval and MBPP as standard function-from-description benchmarks, evaluated with EvalPlus’s HumanEval+ and MBPP+ expanded tests. Make pass@1 the primary metric: the proportion of problems for which one sampled completion passes all tests. Report pass@k (for a prespecified k within the shared generation budget) as secondary, using the standard unbiased estimator when estimating it from multiple samples. The primary sources are Chen et al., “Evaluating Large Language Models Trained on Code” (HumanEval), Austin et al., “Program Synthesis with Large Language Models” (MBPP), and Liu et al., “Is Your Code Generated by ChatGPT Really Correct? Rigorous Evaluation of Large Language Models for Code Generation” (EvalPlus).

**F24 exact passage:**

> Give every model the same per-task prompt, Python environment, decoding settings, and sampling budget. Generate the same number of independent completions per task for each model—typically 200 for estimating pass@1 and pass@10—using a fixed temperature and documented maximum output length. Do not cherry-pick or repair outputs. Execute each completion against the official tests in a sandbox with time and resource limits; count a completion as correct only if it passes all tests. Compute pass@k using the unbiased estimator from the HumanEval paper, aggregating across tasks, rather than treating the 200 samples as a simple success rate for k>1.

Evidence: [humaneval](https://arxiv.org/pdf/2107.03374) — Section 2, pp.2–3; arXiv metadata. Chen et al. 2021 introduces Python docstring function completion and test-based functional correctness. The paper uses n=200, n≥k, and the stated combinatorial unbiased pass@k estimator averaged over problems.; [humanrepo](https://github.com/openai/human-eval) — README, Usage example. Official repository releases evaluation data/code and demonstrates 200 samples per task; tests are public, although they are withheld from the generation prompt.

### FUNCTION-EXPANDED — supported

HumanEval+/EvalPlus expanded tests and MBPP/MBPP+ exist; Chen 2021, Austin 2021, Liu 2023 names identify genuine primary works.

MBPP+ is supported by the continuing EvalPlus project; do not infer that every current MBPP+ release was introduced in the original 2023 HumanEval+ paper. Exact version pinning remains necessary, as the answers say.

**F04 exact passage:**

> Use **HumanEval**, a benchmark of Python function-completion tasks with signatures, docstrings, and executable tests. Prefer the expanded **HumanEval+** tests for stronger correctness checks, recording the exact version. Evaluate every model yourself against the same suite; published scores using different tests or settings are not directly comparable.

**F08 exact passage:**

> **Benchmark and metric.** Use HumanEval for docstring-to-standalone-Python generation, with the expanded HumanEval+ tests from EvalPlus. Make pass@k at a preregistered, shared generation budget k the primary metric: the fraction of tasks for which at least one of k candidates passes every test. Report pass@1 alongside it. Use MBPP as a secondary generalization check, keeping its results separate.

**F08 exact passage:**

> **Confidence and sources.** High confidence for this task format. Primary sources: Chen et al. (2021), introducing HumanEval; Austin et al. (2021), introducing MBPP; Liu et al. (2023), introducing EvalPlus. Suspected contamination or a different deployment workload would shift emphasis toward private evaluation.
> 

**F16 exact passage:**

> **(1) Evaluation and metric.** Use HumanEval and MBPP as standard function-from-description benchmarks, evaluated with EvalPlus’s HumanEval+ and MBPP+ expanded tests. Make pass@1 the primary metric: the proportion of problems for which one sampled completion passes all tests. Report pass@k (for a prespecified k within the shared generation budget) as secondary, using the standard unbiased estimator when estimating it from multiple samples. The primary sources are Chen et al., “Evaluating Large Language Models Trained on Code” (HumanEval), Austin et al., “Program Synthesis with Large Language Models” (MBPP), and Liu et al., “Is Your Code Generated by ChatGPT Really Correct? Rigorous Evaluation of Large Language Models for Code Generation” (EvalPlus).

Evidence: [humaneval](https://arxiv.org/pdf/2107.03374) — Section 2, pp.2–3; arXiv metadata. Chen et al. 2021 introduces Python docstring function completion and test-based functional correctness. The paper uses n=200, n≥k, and the stated combinatorial unbiased pass@k estimator averaged over problems.; [mbpp](https://arxiv.org/abs/2108.07732) — Abstract and metadata. Austin et al., Program Synthesis with Large Language Models, submitted August 2021, introduces MBPP for short Python programs from natural-language descriptions.; [evalplus](https://arxiv.org/abs/2305.01210) — Abstract and metadata. Liu et al. 2023 introduces EvalPlus and HumanEval+ expanded tests, documenting detection of incorrect code missed by original tests.; [evalrepo](https://github.com/evalplus/evalplus) — README, updates and evaluation usage. The project supports both HumanEval+ and MBPP+; MBPP+ exists in later project versions. The 2023 paper abstract focuses on HumanEval+.

### VISION-ID — supported

Standard ImageNet-C has 15 corruptions, four categories and five severities on ImageNet validation images, ICLR 2019.

The standard suite is 15; four additional validation corruptions do not contradict this. F03’s CIFAR alternatives are valid benchmark names in the official robustness project but their full inventory was not independently checked in this bounded audit.

**F03 exact passage:**

> 1. Benchmark and metrics. Use ImageNet-C if both classifiers predict ImageNet’s 1,000 classes; otherwise use the corresponding CIFAR-10-C or CIFAR-100-C benchmark. ImageNet-C covers 15 standard corruption types across noise, blur, weather and digital families, each at five severities. Freeze models and preprocessing before evaluation. Report clean top-1 error, error for every corruption–severity combination, and each type’s mean error across severities. Report mean corruption error (mCE) as a secondary summary, documenting its reference normalization. Primary source: Hendrycks and Dietterich, “Benchmarking Neural Network Robustness to Common Corruptions and Perturbations” (ICLR 2019).

**F06 exact passage:**

> Use ImageNet-C as the primary benchmark, with its standard ImageNet validation images and 15 corruption types across noise, blur, weather, and digital corruption, each at five severity levels. Evaluate both classifiers on exactly the same images, preprocessing, and corruption realizations; also report clean ImageNet validation accuracy so robustness is interpreted alongside ordinary accuracy. ImageNet-C’s mean Corruption Error (mCE) is a useful summary for comparison with prior work, but it should not be the sole score: its normalization against AlexNet can obscure absolute performance.

**F12 exact passage:**

> Use **ImageNet-C** if both classifiers predict ImageNet’s 1,000 classes. It applies 15 common corruption types, grouped into noise, blur, weather, and digital effects, at five severity levels to ImageNet validation images. Keep preprocessing and evaluation images identical, freeze both models, and do not tune on the benchmark’s corrupted evaluation images.

**F20 exact passage:**

> **1) Benchmark and metrics.** Use ImageNet-C (Hendrycks and Dietterich, 2019), which applies 15 corruption types spanning noise, blur, weather, and digital artifacts at five severity levels to ImageNet validation images. Report top-1 accuracy for every corruption type and severity, plus clean ImageNet accuracy. Summarize with mean corruption error (mCE) only as a secondary aggregate; also report the average accuracy drop from clean for each type. Compare models on identical images and corruption realizations, with uncertainty intervals from paired bootstrap resampling over source images.

Evidence: [imagenetc](https://arxiv.org/pdf/1903.12261) — Sections 4.1–4.2; Table 1; Appendix D. Hendrycks and Dietterich, ICLR 2019: ImageNet-C has 15 standard corruption types on ImageNet validation images, four groups, five severities; mCE averages corruption errors normalized against AlexNet. Additional validation corruptions exist outside the standard 15.

### VISION-MCE — supported

mCE is a normalized aggregate, with AlexNet reference normalization.

Per-type/severity reporting, simultaneous inference and clean-performance tradeoffs are proposed analysis choices. Aggregate mCE does not logically imply every type improves; the source explicitly treats corruption types separately.

**F03 exact passage:**

> 1. Benchmark and metrics. Use ImageNet-C if both classifiers predict ImageNet’s 1,000 classes; otherwise use the corresponding CIFAR-10-C or CIFAR-100-C benchmark. ImageNet-C covers 15 standard corruption types across noise, blur, weather and digital families, each at five severities. Freeze models and preprocessing before evaluation. Report clean top-1 error, error for every corruption–severity combination, and each type’s mean error across severities. Report mean corruption error (mCE) as a secondary summary, documenting its reference normalization. Primary source: Hendrycks and Dietterich, “Benchmarking Neural Network Robustness to Common Corruptions and Perturbations” (ICLR 2019).

**F06 exact passage:**

> Use ImageNet-C as the primary benchmark, with its standard ImageNet validation images and 15 corruption types across noise, blur, weather, and digital corruption, each at five severity levels. Evaluate both classifiers on exactly the same images, preprocessing, and corruption realizations; also report clean ImageNet validation accuracy so robustness is interpreted alongside ordinary accuracy. ImageNet-C’s mean Corruption Error (mCE) is a useful summary for comparison with prior work, but it should not be the sole score: its normalization against AlexNet can obscure absolute performance.

**F12 exact passage:**

> - Clean top-1 accuracy for both models.
> - Top-1 error for every corruption–severity pair, plus each corruption’s error averaged equally across its five severities.
> - The new-minus-baseline error difference for each corruption; negative values indicate improvement. Include clean-to-corrupted accuracy drops to show whether gains accompany better clean performance.
> - Overall mean corruption error (mCE), using the benchmark’s reference normalization, as a secondary summary. An improved aggregate cannot establish improvement for every corruption.

**F20 exact passage:**

> **1) Benchmark and metrics.** Use ImageNet-C (Hendrycks and Dietterich, 2019), which applies 15 corruption types spanning noise, blur, weather, and digital artifacts at five severity levels to ImageNet validation images. Report top-1 accuracy for every corruption type and severity, plus clean ImageNet accuracy. Summarize with mean corruption error (mCE) only as a secondary aggregate; also report the average accuracy drop from clean for each type. Compare models on identical images and corruption realizations, with uncertainty intervals from paired bootstrap resampling over source images.

Evidence: [imagenetc](https://arxiv.org/pdf/1903.12261) — Sections 4.1–4.2; Table 1; Appendix D. Hendrycks and Dietterich, ICLR 2019: ImageNet-C has 15 standard corruption types on ImageNet validation images, four groups, five severities; mCE averages corruption errors normalized against AlexNet. Additional validation corruptions exist outside the standard 15.

### MATH-ID — supported

MATH consists of competition math problems with worked solutions, test split, subject/difficulty labels; Hendrycks et al. 2021.

Human logical-correctness grading is newly proposed, not falsely represented as MATH’s standard score. The source supports high-school competition origins; F11’s additional phrase about some problems extending beyond typical high-school competitions is unresolved interpretive scope, not established error.

**F07 exact passage:**

> **Recommendation.** Use the test split of MATH (Hendrycks et al., 2021), a public collection of competition mathematics problems with worked solutions, as the primary evaluation set. Compare both assistants on identical prompts and decoding settings, retaining full written solutions. Report exact-answer accuracy, but make blinded human assessment of logical correctness the primary outcome: independent mathematics graders should mark whether each inference is valid, whether the argument addresses the problem, and whether the final answer follows. Predefine a rubric, adjudicate disagreements, and report agreement and paired differences with confidence intervals. The benchmark’s reference solutions can inform review but should not be treated as the only valid proof.

**F11 exact passage:**

> Recommend MATH’s held-out test split as the public problem resource, stratified by topic and difficulty. Its competition problems and reference solutions suit the setting, although some extend beyond typical high-school competitions. Primary source: Hendrycks et al., “Measuring Mathematical Problem Solving With the MATH Dataset” (2021).

**F19 exact passage:**

> Use the public MATH benchmark (Hendrycks et al.), restricting the evaluation to its competition-style algebra, geometry, number theory, and counting problems. It provides a reproducible problem set and difficulty labels, but its usual exact-answer metric is insufficient for a claim about written reasoning. Publish the selected problem IDs, prompts, both assistants’ outputs, the rubric, and adjudication protocol; disclose any overlap with training data and report results separately for likely-contaminated items if known.

**F22 exact passage:**

> Use the public **MATH benchmark**, which contains high-school competition mathematics problems, difficulty labels, and reference worked solutions. Evaluate on its test split, or a preregistered sample stratified by topic and difficulty. Final-answer accuracy alone cannot establish your claim about written solutions.

Evidence: [math](https://arxiv.org/pdf/2103.03874) — Abstract and dataset description; arXiv metadata. Hendrycks et al. 2021 introduces MATH competition problems with worked solutions, train/test partition, subject and difficulty labels, and final-answer accuracy. The source describes high-school competitions.

### MATH-METRIC — supported

Final-answer accuracy and validity of a complete written solution are different outcomes.

The original benchmark reports answer accuracy; the logical limitation follows from the outcome definition. Proposed graders and rubrics are excluded from factual verification.

**F07 exact passage:**

> **Claim and decision.** This design tests whether the new assistant produces more logically correct written solutions on MATH-like high-school competition problems. A statistically reliable improvement in the blinded correctness rating would support that bounded claim and a decision to prefer it for this use case. Exact-answer gains alone would support answer accuracy, not improved reasoning or proof validity.

**F11 exact passage:**

> The primary metric should be the proportion of generated solutions judged logically correct throughout, rather than final-answer accuracy. Have two mathematics-qualified reviewers independently assess anonymized, randomly ordered outputs using a preregistered rubric: valid inferences, justified assumptions, correct calculations, and no consequential gaps. Accept valid alternative proofs; distinguish minor presentation defects from substantive errors. Adjudicate disagreements and report initial reviewer agreement. Report final-answer accuracy and substantive-error categories as secondary outcomes.

**F19 exact passage:**

> Use the public MATH benchmark (Hendrycks et al.), restricting the evaluation to its competition-style algebra, geometry, number theory, and counting problems. It provides a reproducible problem set and difficulty labels, but its usual exact-answer metric is insufficient for a claim about written reasoning. Publish the selected problem IDs, prompts, both assistants’ outputs, the rubric, and adjudication protocol; disclose any overlap with training data and report results separately for likely-contaminated items if known.

**F22 exact passage:**

> Use the public **MATH benchmark**, which contains high-school competition mathematics problems, difficulty labels, and reference worked solutions. Evaluate on its test split, or a preregistered sample stratified by topic and difficulty. Final-answer accuracy alone cannot establish your claim about written solutions.

Evidence: [math](https://arxiv.org/pdf/2103.03874) — Abstract and dataset description; arXiv metadata. Hendrycks et al. 2021 introduces MATH competition problems with worked solutions, train/test partition, subject and difficulty labels, and final-answer accuracy. The source describes high-school competitions.

### MAINTAINER-SWE — supported

SWE-bench uses real GitHub issues; Verified contains human-validated tasks and resolution is test-based.

Jimenez et al. 2024 is the conference year, not an erroneous claim of first arXiv release in 2024. The answers do not assert a Verified release date. Maintainer time and approval are outside this automated benchmark’s measured outcome.

**F05 exact passage:**

> 1) **Evaluation and metric.** Use a randomized, within-maintainer crossover study on real, unresolved issues from the target repositories, stratified by repository and issue difficulty. Each maintainer solves comparable issues with the current assistant and the new assistant, with order randomized. The primary metric should be **active maintainer time from task start to an independently reviewed, acceptable fix**; define acceptance in advance (tests and maintainer review) and count failures as not accepted, not as zero-time wins. Report acceptance rate and time-to-acceptance together, with uncertainty intervals. SWE-bench Verified is a useful secondary benchmark: it contains real GitHub issues and human-validated tasks, and its test-based resolution rate can check whether agents produce fixes that pass tests. It does not measure maintainer time or approval. Relevant primary source names: SWE-bench (Jimenez et al., 2024) and the SWE-bench Verified release by OpenAI.

**F10 exact passage:**

> Use a randomized maintainer study as the decisive evaluation. Sample fresh, realistic issues from participating established Python repositories. Supplement this with SWE-bench Verified’s resolved-task rate for reproducibility, not as proof of time savings. Primary sources: Jimenez et al., *SWE-bench* (ICLR 2024), and OpenAI’s SWE-bench Verified release.

Evidence: [swe](https://arxiv.org/abs/2310.06770) — Abstract and metadata. Jimenez et al. SWE-bench consists of real GitHub issues and corresponding pull requests from Python repositories. Initial arXiv submission is October 2023; ICLR conference publication is 2024.; [verified](https://www.swebench.com/verified.html) — Overview. SWE-bench Verified is a human-filtered subset created with OpenAI; annotators reviewed clarity, test-patch correctness and task solvability. It evaluates coding-agent issue resolution, not human maintainer time.

### PHYSICS-SOURCES — supported

ALCE/Gao 2023 and FActScore/Min 2023 are genuine citation-quality and atomic-factuality methods.

Both responses qualify transfer to physics. FActScore does not itself validate physics or establish bibliographic existence, and neither response claims it does.

**F02 exact passage:**

> **Benchmark and metrics.** Build a held-out physics literature-review benchmark spanning subfields, difficulty, and publication dates, with independently assembled evidence. Use **verified claim support rate** as primary: the fraction of citation-required atomic scientific claims supported by at least one real, correctly identified cited paper. Missing, fabricated, and nonsupporting citations earn no credit. Separately report invented-reference rate among unique references, citation-link entailment precision, citation coverage, and review completeness. ALCE (Gao et al., 2023) provides citation-evaluation methodology; FActScore (Min et al., 2023) provides atomic-claim evaluation methodology. Neither substitutes for physics validation.

**F15 exact passage:**

> Use a held-out, physics-specific literature-review set with expert-written review questions, a fixed corpus snapshot, and gold papers plus claim-level evidence passages. Add SciFact (Wadden et al., 2020) as a public, adjacent benchmark for scientific claim/evidence verification; it is not a physics literature-review benchmark. For end-to-end attribution, ALCE (Gao et al., 2023) provides an evaluation framework for citation quality, though its settings may not match scholarly references.

Evidence: [alce](https://aclanthology.org/2023.emnlp-main.398/) — Abstract and metadata. Gao et al. 2023, Enabling Large Language Models to Generate Text with Citations, introduces ALCE and citation-quality evaluation for end-to-end retrieval and answer generation.; [factscore](https://aclanthology.org/2023.emnlp-main.741/) — Abstract and metadata. Min et al. 2023 introduces atomic-fact decomposition and the percentage supported by a reliable source; evaluation includes generated biographies, not physics reviews.

### PHYSICS-SCIFACT — supported

SciFact/Wadden 2020 is an adjacent scientific claim/evidence verification benchmark, small and mostly biomedical, not physics literature review.

Small is relative language; the primary source provides the scale. The paper confirms biomedical focus and claim–abstract support/refutation. No primary contradiction found.

**F15 exact passage:**

> Use a held-out, physics-specific literature-review set with expert-written review questions, a fixed corpus snapshot, and gold papers plus claim-level evidence passages. Add SciFact (Wadden et al., 2020) as a public, adjacent benchmark for scientific claim/evidence verification; it is not a physics literature-review benchmark. For end-to-end attribution, ALCE (Gao et al., 2023) provides an evaluation framework for citation quality, though its settings may not match scholarly references.

**F15 exact passage:**

> This combination tests factual reference existence and claim support, not completeness, novelty, or review quality. SciFact is small and mostly biomedical, so it cannot establish physics performance. A custom expert-annotated set is necessary; this plan is sufficient for the stated comparative claim if its size and inter-rater agreement support a precise estimate.

Evidence: [scifact](https://aclanthology.org/2020.emnlp-main.609.pdf) — Sections 2–3, pp.2–3; Appendix C.1. Wadden et al. 2020 introduces scientific claim–abstract evidence verification. The dataset has 1,409 claims and biomedical focus, with journal sources ranging from basic science to clinical medicine.

## Limits

The check was bounded to approximately four minutes of primary-source retrieval and synthesis. All responses were read, but no per-document WMT timestamp extraction, current benchmark execution, exhaustive test-suite analysis, or empirical validation of proposed statistical designs was performed. No absence of retrieval evidence is treated as an error. F11’s beyond-typical-high-school qualifier remains unresolved. F24’s hidden tests are prompt-hidden but publicly released. CIFAR corruption inventories were not independently enumerated. No primary recommendation rating was assigned.

Additional primary identity check: the [official robustness repository](https://github.com/hendrycks/robustness) explicitly links CIFAR-10-C/CIFAR-100-C and states the 1,000-class ImageNet-C label space (retrieved line193).
