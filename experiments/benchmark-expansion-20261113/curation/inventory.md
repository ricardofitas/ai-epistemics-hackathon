# Pilot breadth inventory

Snapshot before the new five-case block. The defensible audited unit is a source-backed research-claim family with actual recommendation answers, not every named benchmark or a full model-performance benchmark run.

**10 existing tested source-case families; 102 complete answers in 106 captures.** Four captures are empty/incomplete API calls. WMT contributes one family despite 38 captures and 34 final answers.

| Family | Resource anchors | Complete answers |
|---|---|---:|
| civilcomments | CivilComments/WILDS | 16 |
| truthfulqa_mc2 | TruthfulQA MC2 | 8 |
| function_correctness | HumanEval/EvalPlus or MBPP alternatives | 8 |
| maintainer_time | SWE-bench as partial proxy | 8 |
| citation_support | ALCE as partial proxy | 8 |
| translation_source_period | WMT19/WMT20 | 34 |
| mathematical_process_correctness | MATH/PRM800K as one source family | 8 |
| each_corruption_robustness | ImageNet-C | 8 |
| real_query_extraction | Natural Questions | 2 |
| adult_symptom_triage | Semigran 45-vignette resource, MIMIC-IV-ED adapted clinical cases | 2 |

HANS currently has a source/score reanalysis only; the new role-sensitive NLI prompt converts it into an actual recommendation pilot. The triage case was keyed under MedQA, but its two real recommendations were Semigran and MIMIC-IV-ED; do not count those as two independent scenarios or call them MedQA recommendations. MATH/PRM800K, WMT year variants, and evaluator implementations remain grouped.

The proposed five new families bring coverage to **15 source-case families if all are actually sampled**. Recommend **12 well-reviewed families as the minimum and 15 as the preferred pre-hackathon target**. Beyond that, prioritize replication, source-verification correction and downstream consequences over adding names. Twenty calls mean one initial answer from four configurations on five case prompts; they do not estimate a broad error rate.

Next steps: freeze prompts and source-backed criteria; run all20 planned calls; retain nulls/transport failures; blind-score and fact-check; replicate the strongest new failures; seek human adjudication before paper claims.
