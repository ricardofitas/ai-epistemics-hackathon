# Exploratory pre-sprint pilot: MNLI and HANS

**Prepared:** 2026-11-12, before the AI × Epistemics Research Sprint.  
**Status:** Independent source audit and reanalysis of published model results. No research-assistant recommendation has been tested. Mark this as pre-existing work if used in a sprint report.

## The evaluation mismatch

MNLI is a natural language inference (NLI) dataset. HANS was designed to test whether NLI models rely on lexical overlap, subsequence and constituent heuristics when those heuristics lead to wrong conclusions. A specific HANS category swaps subject and object while retaining the same words: “the doctor visited the lawyer” does not entail “the lawyer visited the doctor.” Sources: [HANS paper](https://aclanthology.org/P19-1334/) and [100 BERT runs paper](https://aclanthology.org/2020.blackboxnlp-1.21/).

McCoy, Min and Linzen fine-tuned 100 instances of BERT on MNLI. They changed the classifier initialization and training-example order while keeping the pretrained BERT weights and other training choices fixed. Their matched MNLI development scores ranged from 83.667856% to 84.76821%, but subject–object swap accuracies in HANS ranged from 0% to 66.2%. The MNLI development split was used as a held-out evaluation set, not the unavailable-label MNLI test split. Source: [paper](https://aclanthology.org/2020.blackboxnlp-1.21.pdf), §§3–4.

## A reproducible decision example

I reanalyzed the authors' [run-level CSV](https://github.com/tommccoy1/hans/blob/master/berts_of_a_feather/berts_of_a_feather_accuracies_by_run.csv), using [their README](https://github.com/tommccoy1/hans/tree/master/berts_of_a_feather) to identify columns. Among the 100 runs there are 53 pairs with *identical* reported MNLI development accuracy. The median absolute difference in subject–object swap accuracy among these tied pairs is 16.2 percentage points; 17 of the 53 pairs differ by at least 20 points. Pairs overlap, so these counts are descriptive and must not be treated as independent trials.

The largest swap gap among exactly tied MNLI pairs is this deliberately selected **illustrative extreme**:

| Published run | MNLI matched dev | Overall HANS | HANS subject–object swap |
| --- | ---: | ---: | ---: |
| 37 | 84.411615% | 60.886667% | 62.5% |
| 72 | 84.411615% | 54.513333% | 1.3% |

A rule based only on MNLI cannot distinguish runs 37 and 72. A rule requiring performance on the subject–object swap construction favors run 37 by **61.2 percentage points** on that published challenge subcategory. The overall HANS difference is about **6.37 points**, so the subcategory score is useful when the claim names that precise failure mode. This comparison does not show how any AI assistant would recommend a benchmark and does not establish broad real-world syntactic ability.

The script [`scripts/analyze_hans_runs.py`](../../scripts/analyze_hans_runs.py) recomputes the counts and pair from the upstream CSV without downloading model weights. For example:

```bash
python3 scripts/analyze_hans_runs.py berts_of_a_feather_accuracies_by_run.csv
```

Only rows named `Run 0` to `Run 99` are included; the upstream CSV also contains summary and blank rows. The data are linked rather than copied into this repository.

## Pilot questions for research assistants

Provide the *same* short descriptions of MNLI matched development accuracy, HANS overall accuracy, and HANS subject–object swap accuracy to each model. Ask which evaluation supports the claim, what it leaves unresolved, and whether another evaluation is needed. Keep the published run scores out of the recommendation prompt; use them afterwards for the retrospective decision example.

| Variant | Scientific claim or decision | Expected assessment for an independent reviewer |
| --- | --- | --- |
| H-INDIST | Select the run with highest performance on the MNLI matched development distribution. | MNLI matched development accuracy fits this stated decision. |
| H-SWAP | Select the run best at rejecting non-entailment cases formed by swapping subject and object. | The specific HANS subject–object swap subcategory is the direct test. MNLI matched accuracy and HANS aggregate alone are less informative for this precise goal. |
| H-HEUR | Evaluate susceptibility to the three heuristics targeted by HANS. | HANS plus category breakdown is appropriate; MNLI alone is insufficient. |
| H-GENERAL | Establish robust syntactic reasoning on arbitrary natural text and future domains. | HANS is useful but partial evidence: its controlled constructions target specific heuristics. Additional, differently sourced tests are needed for the broad claim. |

A model may correctly recommend both MNLI and HANS when the question calls for in-distribution performance *and* syntactic challenge performance. Do not mark every MNLI mention as an error. Reserve separate source cases for the main study if these prompts are used to tune the intervention or scoring rubric.

## Status and limits

This is a **real reanalysis of existing experimental data**, not an experiment on research assistants. The paper already reported the broad performance gap; the exactly matched pair and tied-pair counts above are my exploratory calculations from its released CSV. The maximum gap was selected after inspecting all tied pairs, so it illustrates a possible decision consequence rather than a typical effect. HANS tests a controlled set of heuristics; the source papers do not claim comprehensive syntax or deployment validity. The next empirical step is to collect and blindly score assistant recommendations on this and independently sourced cases.
