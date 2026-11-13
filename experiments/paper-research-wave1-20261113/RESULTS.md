# Paper-oriented research wave — 13 November 2026

The frozen 60-attempt native Adaption wave produced **53 complete recommendation answers and seven empty max-output-token incompletes**. After independent first agent reviews, factual checks and explicit scope adjudication, the primary labels are **12 yes, 36 no, five uncertain, seven unscorable**. Human review is pending. These are selected and heterogeneous case counts, not a population error estimate or a model ranking.

Coverage increased from **15 to 21 source-backed recommendation case families**. The next breadth target is 25; four proposals are prepared, with the localization slot still operationally provisional. Repetitions, alternative benchmark names and wording probes add zero families. This inventory is not a count of complete candidate-model benchmark executions.

## What strengthened

**Temporal mismatch recurred.** WMT19/newstest2019 was recommended for late-2019 news in seven complete answers, including one mixed WMT19-or-WMT20 endorsement. The official WMT19 page specifies a September–November 2018 collection window and April 2019 release; WMT20 specifies September–November 2019. The release date independently excludes the requested late-2019 source period. These are documentation windows, not an article-by-article timestamp audit. The benchmark remains a valid resource for its actual task. [WMT19](https://www.statmt.org/wmt19/translation-task.html); [WMT20](https://www.statmt.org/wmt20/translation-task.html).

**A statistical-inference error recurred.** Two DeepSeek requested-configuration answers explicitly inferred equivalence from nonsignificance while using an otherwise suitable TREC-COVID top-ten evaluation. A third answer with the phrase no-difference conclusion was reduced from both first agents’ yes to uncertain after a plausible no-detected-difference reading was identified. Nonsignificance alone cannot establish a meaningful equivalence bound. This is a known inference error in advice, not a TREC-COVID defect. [Lakens 2017](https://pmc.ncbi.nlm.nih.gov/articles/PMC5502906/).

Each cell below planned **three** fresh original-question requests. Fractions are exact target-mechanism yes / complete captures. Missing captures do not count as scientific errors or as successful recurrence.

| Requested configuration | Wrong WMT source period | Nonsignificance → equivalence | PAWS score → directional NLI |
|---|---:|---:|---:|
| gemma-4-31b-it | 3/3 | 0/3 | 0/3 |
| deepseek-v4-flash | 2/3 | 2/3 | 0/3 |
| glm-5.2 | 1/3 | 0/3 | 0/1 |
| qwen3.8-27b | 1/1 | 0/2 | 0/3 |

The prespecified ≥2/3 same-mechanism flag is met for WMT in Gemma and DeepSeek, and for statistical equivalence in DeepSeek. It is a descriptive prioritization rule, not significance, prevalence, stable weights, or a publication guarantee. Model aliases are recorded requested configurations; immutable checkpoints are unavailable. SSE transport and the WMT token budget differ from earlier cohorts, so this is recurrence under the newly recorded settings.

## What did not replicate

The earlier PAWS-paraphrase-as-directional-NLI mechanism appeared **zero times among ten complete answers / 12 attempts**. Three configurations had all three complete contexts and zero exact recurrences. GLM had one complete and two incomplete contexts. Therefore the separately prepared 24-call PAWS/HANS performance pilot was **not executed under the prespecified gate**. No candidate scores, ranking reversal or target-selection consequence were measured. A different Qwen role-case error does not activate that gate. See [NOT_RUN_STATUS.json](consequence/NOT_RUN_STATUS.json).

## Three new S0 observations

| Response | Observation | Current support and limit |
|---|---|---|
| Q40 / PR-01, DeepSeek | Describes full SVAMP as harmless numerical/paraphrase changes preserving the same structure, then treats aggregate accuracy as evidence for that specific robustness claim. | Primary SVAMP Table 1 includes reasoning-changing and question-changing edits. No controlled matching subset is specified. Independently source/scope checked; one answer for this mechanism. |
| Q48 / PR-11, Qwen | Converts every non-gold WSC pronoun substitution to contradiction and treats neutral as wrong. | Original coreference labels do not universally establish contradiction. An authentic official SuperGLUE v2 witness and separate logical counterworld are preserved; no official three-way NLI gold or model-performance consequence is asserted. One of three role-case contexts, different from the old PAWS mechanism. |
| Q50 / PR-42, Gemma | A useful controlled GSM8K perturbation plan is said to distinguish true reasoning from pattern matching/memorization. | Finite answer robustness does not identify that internal process. The bounded robustness conclusion remains valid, while the stronger surviving assertion exceeds frozen GSMR-C4. One answer for this mechanism. |

The SVAMP source explicitly distinguishes structural-invariance and reasoning-changing variants. A validated subset or custom adaptation can be appropriate; the error concerns the recommendation’s stated aggregate and conclusion. [SVAMP primary paper](https://aclanthology.org/2021.naacl-main.168.pdf). The authentic WSC records and original coreference labels are in [WSC_LABEL_CONVERSION_WITNESS.json](reviews/WSC_LABEL_CONVERSION_WITNESS.json); its additional entailment analysis is a logical warrant, not a relabelled official benchmark.

## Six new families, including aligned outcomes

| Source-case family | Complete / attempted | Yes | No | Uncertain |
|---|---:|---:|---:|---:|
| FActScore + important-fact coverage | 4/4 | 0 | 3 | 1 |
| DROP / discrete passage answers | 4/4 | 0 | 3 | 1 |
| Arithmetic perturbation robustness | 3/4 | 2 | 1 | 0 |
| SQuAD2 answer / abstain | 4/4 | 0 | 4 | 0 |
| ScienceWorld executed goals | 4/4 | 0 | 4 | 0 |
| Preference vs scientific factuality | 3/4 | 0 | 3 | 0 |

The screen produced no clear precision-as-important-coverage substitution, no goal-terminal-equals-success error, and no preference-equals-factual-truth error in these sampled answers. DROP has one unresolved custom-evaluation scope; FActScore has one unresolved statistical-preservation rule. Source auditing also found ancillary citation/count/default/signature inaccuracies. These are recorded separately and are not automatically added to the material-error numerator.

## Review and claim scope

- Original rubric and critical requirements were frozen before sampling; stronger evidence stages never add adverse response requirements retroactively.
- Two independent first agent files were hashed and committed at **d592e6df7d8aef413ece3b3986b75f75f1b7b49e**, before coordinator label/key analysis. They each assigned 13 yes; originals remain unchanged.
- The two primary first disagreements, Q20 and Q59, remain uncertain. A separate coordinator disposition changes agreed-yes Q47 to uncertain. Full factual audit, model-blinded scope assessment and exact quotations are preserved.
- Narrow resource-fit claims use only the corresponding subset, rather than all 12 primary errors. The post-hoc type partition is WMT7 + SVAMP1 resource fit; WSC1 label conversion; equivalence2; internal-process overclaim1. Removing mixed WMT Q46 leaves 11 primary yes and six WMT yes; Gemma/DeepSeek WMT ≥2/3 flags survive with planned denominators retained. See sensitivity artifacts.
- This is a curated source-grounded advice audit with post-discovery selection, shared domain clusters, dependent same-family agent review, and incomplete stage blinding. It does not establish representative prevalence, new intrinsic benchmark defects, real-user harm, or a general model ranking.
- Closely related work already studies inappropriate evaluation choices; novelty must come from the concrete audit, recurrence and eventual interventions/consequences, within the declared setting. See [RELATED_WORK.md](RELATED_WORK.md).

## Integrity and reproduction

All 60 payload/text/individual-artifact/aggregate/SSE-journal audits passed, with all starts after freeze **576bd7a1ab31024464f81368f51800b712564c14** at 04:20:31Z. Seven provider response.completed envelopes carried status=incomplete/max_output_tokens and empty text; both signals are retained and completion stays false. No retries, delta fallback, substitutions or early stopping. All complete answers obeyed the 300-word cap.

The 126,472,340 original journal bytes are preserved losslessly in a 6 MB deterministic gzip/base64 archive, and all 60 restored hashes were independently compared. The original frozen tree’s 323 paths were preserved unchanged when 226 capture/review/method files were added. The four generic OK transport probes are excluded from recommendation and family counts. Provider reported usage.cost sums to 0.340781867; account debit, completeness of billing and USD equivalence are unverified.

See [REPRODUCE.md](REPRODUCE.md), [analysis_summary.json](analysis_summary.json), [coverage-after.json](coverage-after.json), [first_review_freeze.json](reviews/first_review_freeze.json), and [adjudication.json](reviews/adjudication.json). A declared sample of 27 answers, including ten random final-no controls, is prepared for independent human review; no human ratings have been obtained.

## Next evidence step

1. Source/fidelity review and freeze the four additional coverage candidates, then screen all 16 planned case/configuration cells. Localization stays provisional until source delivery/scorer issues are resolved; the count rises only after actual interpretable answers.
2. Characterize repeated behavior with separately frozen additional contexts, retaining incompletes and all original outcomes. The planned two-context extension of all 12 selected cells adds 24 attempts; cells missing earlier complete contexts cannot be called five-complete-context evidence.
3. Freeze and sample the six fidelity-reviewed unused wording probes across four configurations (24 attempts), then design balanced source-evidence versus baseline/generic-caution comparisons on mature cases. These add no new source families.
4. Obtain scoped human/source validation and repeat the three new S0 mechanisms before stronger claims or actual consequence pilots. Keep the failed PAWS activation and historical null ranking results visible.
