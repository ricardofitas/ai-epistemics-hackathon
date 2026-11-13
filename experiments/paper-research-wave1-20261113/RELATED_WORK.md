# Related work and novelty check — 13 November 2026

The strongest defensible direction is **a source-grounded audit of benchmark–claim fit in LLM research advice**. Existing work already demonstrates bad benchmark selection by autonomous AI scientists and establishes the conceptual/statistical mistakes appearing in these pilots. More benchmark names and isolated errors alone do not establish a new paper contribution.

This is a targeted search of primary sources, with a recent-coverage verification search, rather than an exhaustive systematic review. Bibliographic metadata and overlap were checked against original articles, author uploads, or official proceedings. The machine-readable companion records verification depth and exact identifiers: [related_work.json](related_work.json).

## Six closest or directly necessary primary works

| Work | Exact relationship to this project | What additional evidence could contribute |
|---|---|---|
| **Luo, Kasirzadeh & Shah (2026)**, *The more you automate, the less you see: Hidden pitfalls of autonomous AI scientists*. PNAS. [Article](https://pmc.ncbi.nlm.nih.gov/articles/PMC13663820/), DOI **10.1073/pnas.2610214123**. | Closest empirical prior: autonomous research pipelines, benchmark-selection biases, metric misuse, and artifact-based auditing. | Real benchmark documentation and ordinary claim-specific assistant advice provide a distinct setting; replication and interventions must establish its empirical value. |
| **Bean et al. (2025)**, *Measuring what Matters: Construct Validity in Large Language Model Benchmarks*. NeurIPS Datasets and Benchmarks. [Proceedings](https://proceedings.neurips.cc/paper_files/paper/2025/hash/1967e0fc3aa6cbbace562f5cb8e3954e-Abstract-Datasets_and_Benchmarks_Track.html), DOI **10.52202/085713-0590**. | A systematic benchmark construct-validity review; direct prior for phenomena/task/metric/claim distinctions. | Study recommendation behavior rather than benchmark authors' design and reporting. Do not claim to invent construct-validity auditing. |
| **Raji, Bender, Paullada, Denton & Hanna (2021)**, *AI and the Everything in the Whole Wide World Benchmark*. NeurIPS Datasets and Benchmarks. [arXiv:2111.15366](https://arxiv.org/abs/2111.15366). | Explains why narrow benchmarks do not justify general capability claims. | Measure when assistants make specific unsupported scope extensions and whether source evidence corrects them. |
| **Ethayarajh & Jurafsky (2020)**, *Utility is in the Eye of the User: A Critique of NLP Leaderboards*. EMNLP. [Proceedings](https://aclanthology.org/2020.emnlp-main.393/), DOI **10.18653/v1/2020.emnlp-main.393**. | Leaderboard utility can diverge from practitioner needs. | Explicit user constraints can become testable recommendation criteria. The underlying insight is established. |
| **Alzahrani et al. (2024)**, *When Benchmarks are Targets: Revealing the Sensitivity of Large Language Model Leaderboards*. ACL. [Proceedings](https://aclanthology.org/2024.acl-long.744/), DOI **10.18653/v1/2024.acl-long.744**. | Demonstrates ranking sensitivity to evaluation protocol details. | Connect an actual assistant recommendation to a measured decision change. The present pilots do not yet demonstrate such a reversal. |
| **Lakens (2017)**, *Equivalence Tests: A Practical Primer for t Tests, Correlations, and Meta-Analyses*. SPPS. [Article](https://pmc.ncbi.nlm.nih.gov/articles/PMC5502906/), DOI **10.1177/1948550617697177**. | Direct methodological prior for nonsignificance versus meaningful equivalence. | Audit a known statistical error in advice. This is neither a new statistical result nor an intrinsic TREC-COVID defect. |

The Luo paper's 2025 arXiv version uses the title *The More You Automate, the Less You See: Hidden Pitfalls of AI Scientist Systems* ([arXiv:2509.08713](https://arxiv.org/abs/2509.08713)); the journal version was published online on 5 October 2026. Treat these as versions of one work. Its official artifact repository is [AIScientistPitfalls](https://github.com/niharshah/AIScientistPitfalls).

## Claim boundaries for the current results

- A WMT source-period mistake is an **observed recommendation/documentation error**. A benchmark's year label need not describe its news collection period. Existence and repeated occurrence can be demonstrated without implying that WMT itself is broken.
- PAWS paraphrase scores being treated as sufficient for directional NLI is a **claim–measurement mismatch**, subject to careful reading of the whole answer. Qualified proxy use, an explicit adaptation, or an accompanying NLI test may be valid. A synthetic counterexample illustrates logic; it is not automatically a PAWS item, a measured model error, or a ranking reversal.
- Nonsignificance being used to conclude user-facing equivalence is a **known inference error**. Correct inference requires a justified practical margin and a suitable analysis for the actual paired retrieval observations.
- These are selected cases, not a probability sample. Report rates within this design, with explicit denominators; do not generalize them to all assistants or all scientific advice. Repeated calls share the same case and are not independent case families.
- Agent review is useful preliminary checking. It cannot be described as human validation, and disagreements should remain visible.

## Raise the evidence bar in stages

1. **Existence and correctness:** preserve verbatim responses, primary-source facts, qualified correct answers, nulls and uncertain outcomes. Freeze scoring rules before new results are inspected.
2. **Recurrence and transfer:** exact-question repeats establish within-case recurrence; paraphrases and held-out source families probe robustness. Report these separately.
3. **Reliable attribution and mitigation:** obtain blinded human double annotation and compare balanced no-source, relevant-source, and generic-caution conditions. A source package should improve specifically source-dependent decisions if that is the proposed mechanism.
4. **Consequences:** use actual dataset examples or fixed candidate models to compare the recommended and correct evaluation decisions. A null ranking result is informative and must remain in the record.

A realistic paper claim, if these stages succeed, is: **“In a curated suite of source-verifiable research-advice scenarios, we measure when assistants recommend evaluations that do not support the stated claim, and test which source interventions reduce those errors.”** A possible title is *When the Benchmark Does Not Support the Claim: Auditing LLM Research Advice*.

At present the project should not claim a new intrinsic benchmark flaw, a general prevalence estimate, a demonstrated decision reversal, or the first observation of poor AI evaluation choices. Those are separate claims with higher evidence requirements. The closest prior work makes transparent empirical design and a demonstrated extension essential to the contribution.
