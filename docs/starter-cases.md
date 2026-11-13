# Starter cases and sources

These are candidate cases, not a finished benchmark. Each requires source checking, a precise prompt, a pre-specified rubric and independent review before use. Public examples illustrate why the question matters; none demonstrates that an AI assistant in this project has made a bad recommendation.

## 1. CivilComments: average versus worst-group accuracy

**Candidate research goal:** compare methods for comment classification, first prioritizing average performance and then explicitly prioritizing the worst-performing group.

**Evidence:** the [WILDS CivilComments leaderboard](https://wilds.stanford.edu/leaderboard/) reports the following test scores without unlabeled data:

| Method | Average accuracy | Worst-group accuracy |
| --- | ---: | ---: |
| ERM, grid search | 92.2% | 56.0% |
| Fish | 89.3% | 75.3% |

Under these reported scores, average accuracy favors ERM by 2.9 percentage points; worst-group accuracy favors Fish by 19.3 points. Inspect leaderboard methodology, definitions, variability and model comparability before analysis. These figures illustrate a metric-dependent choice; they do not prove an actual AI recommendation or downstream deployment outcome.

**Case-building task:** prepare matched prompts with the same benchmark evidence and candidate methods but different objectives. Define how a well-qualified answer may report both metrics. Do not assume that worst-group accuracy alone captures every fairness concern.

## 2. MNLI and HANS: general score versus a specific failure mode

**Candidate research goal:** evaluate whether a model handles a specific syntactic generalization rather than only performing well on an aggregate natural-language inference dataset.

**Evidence:** [McCoy et al. 2019](https://aclanthology.org/P19-1334/) introduce HANS to investigate syntactic heuristics. In a [follow-up study](https://aclanthology.org/2020.blackboxnlp-1.21/), 100 BERT runs had MNLI development accuracy between 83.6% and 84.8%, while accuracy on a specific subject–object swap category ranged from 0% to 66.2%.

**Case-building task:** use the original papers to specify what each dataset can and cannot support. Ask for an evaluation plan for the specific failure mode; allow a combination of MNLI and HANS with appropriate qualifications. The aggregate range alone does not establish a ranking reversal between two particular systems.

## 3. Prior team work: GAMMAF scoring and delivered answers

**Candidate goal:** assess whether an evaluation scores the answer delivered after filtering agents. The prior project identified a potential mismatch between the scored voting population and the delivered answer in a particular GAMMAF implementation.

**Case-building task:** verify the exact version, protocol, dataset, quantitative results and accessible primary sources. Obtain permission before redistributing team artifacts. Treat an implementation defect as distinct from choosing an otherwise valid benchmark for an unsupported claim. This case is optional if provenance or reuse cannot be established during the sprint.

## 4. Missing or partial fit

Create at least one case where the supplied benchmark candidates do not measure a stated critical requirement, and one where the request lacks information needed to decide. Use real benchmark descriptions and pre-register why an added test, qualification or clarification is necessary. The correct response may be conditional or may identify that no supplied option is sufficient; this does not imply that no suitable benchmark exists elsewhere.

## Key references

1. Luo, Z., Kasirzadeh, A., and Shah, N. B. (2026). [The more you automate, the less you see: Hidden pitfalls of autonomous AI scientists](https://pmc.ncbi.nlm.nih.gov/articles/PMC13663820/). PNAS. Direct prior work on benchmark selection, metric-related failures and workflow auditing.
2. Hutchinson, B. et al. (2022). [Evaluation Gaps in Machine Learning Practice](https://facctconference.org/static/pdfs_2022/facct22-3533233.pdf). FAccT.
3. Koh, P. W. et al. (2021). [WILDS: A Benchmark of in-the-Wild Distribution Shifts](https://proceedings.mlr.press/v139/koh21a.html). ICML.
4. McCoy, R. T., Pavlick, E., and Linzen, T. (2019). [Right for the Wrong Reasons](https://aclanthology.org/P19-1334/). ACL.
5. Shen, C. et al. (2026). [One-Eval: An Agentic System for Automated and Traceable LLM Evaluation](https://arxiv.org/abs/2603.09821). Preprint; an example of automated benchmark and metric recommendation.

Search for additional related work on claim–evaluation alignment, benchmark recommendation, measurement validity, calibration and decision consequences before making novelty claims.
