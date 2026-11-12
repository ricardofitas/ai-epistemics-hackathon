# Exploratory pre-sprint pilot: CivilComments-WILDS claim–evaluation fit

**Prepared:** 2026-11-12, before the AI × Epistemics Research Sprint.  
**Status:** Source audit plus a completed [fresh-context agent pilot](civilcomments-agents-20261112.md): 16 responses, no unsupported recommendations under the recorded rubric, two independent agent ratings. The separate API runner below was checked in dry-run mode only. This file and the completed pilot are pre-existing exploratory work and must be identified as such in any sprint submission.

## Verified source facts

- WILDS CivilComments is a binary toxicity classification task. Its eight identity flags indicate whether a *comment mentions* a demographic identity. They do **not** identify the author's demographic group. Source: [WILDS dataset description](https://wilds.stanford.edu/datasets/), CivilComments section, and [WILDS paper supplement](https://proceedings.mlr.press/v139/koh21a/koh21a-supp.pdf), §H.6.1 and §H.6.3.
- WILDS reports average accuracy and worst-group accuracy. The latter is the minimum of the true positive and true negative rates across eight identity-mention categories, yielding 16 potentially overlapping identity × toxicity-label groups. It does not give the full set of 16 rates in the leaderboard. Source: [WILDS supplement](https://proceedings.mlr.press/v139/koh21a/koh21a-supp.pdf), §H.6.1.
- The authors explicitly flag that worst-group accuracy weights false positives and false negatives equally; costs and decision thresholds may matter in deployment, and intersections of identities remain difficult to estimate. Source: [WILDS supplement](https://proceedings.mlr.press/v139/koh21a/koh21a-supp.pdf), §H.6.4.
- The [CivilComments leaderboard](https://wilds.stanford.edu/leaderboard/) (without unlabeled data, test scores; same DistilBERT backbone) lists ERM grid search at **92.2% average / 56.0% worst-group** and Fish at **89.3% average / 75.3% worst-group**. Parentheses on the leaderboard indicate variability across replicates. The [submission guidelines](https://wilds.stanford.edu/submit/) call for five CivilComments replicates. These are published entries from different submissions, not a controlled new experiment.

An additional numerical check from Table 15 of the [WILDS supplement](https://proceedings.mlr.press/v139/koh21a/koh21a-supp.pdf): for the *Group DRO (label)* baseline, accuracy on non-toxic comments mentioning Black identity is 72.2% (standard deviation 2.3 across seeds). Thus its mean false-positive rate on that specific group is 27.8% at the evaluated threshold. This is a group-specific observation for that baseline, **not** a Fish-versus-ERM comparison and not a measurement of false removals of Black authors.

## A retrospective decision contrast (not an AI result)

If the decision rule is highest reported average test accuracy between these two entries, ERM wins by **2.9 percentage points**. If the rule is highest reported worst-group test accuracy, Fish wins by **19.3 percentage points**. This is a change in which method a specified rule would select from *published scores*. It is not evidence that an AI recommended the wrong metric, or that either method is preferable in deployment.

## Candidate paired pilot prompts

Keep the common evidence below identical. Ask each assistant in a fresh context with no browsing, no leaderboard scores and the same output request. Pilot prompts can be revised; record every revision. Do not show the expected answers or this audit to the tested assistant.

**Common evidence supplied to the assistant:**

> We are choosing an evaluation for a binary toxicity classifier. Available public evidence concerns CivilComments-WILDS. Its dataset labels toxicity and flags whether a comment mentions any of eight demographic identities. Its leaderboard provides overall accuracy and worst-group accuracy. The latter is the lowest true positive or true negative rate over 16 identity-mention × toxicity-label groups. You may recommend either reported metric, both with qualifications, a further evaluation, or say that the supplied evidence is insufficient.

**Common output request (both prompting conditions):**

> Which evaluation would you recommend to support the specific claim below? State what it measures, what it cannot establish, and whether more evidence or clarification is required. Give a qualified answer when appropriate.

| Variant | Claim or decision to insert | Defensible response (audit key, not shown to model) |
| --- | --- | --- |
| CC-AVG | “We want to select the classifier with the highest average accuracy on the CivilComments-WILDS test distribution.” | Average accuracy is directly aligned. Worst-group accuracy can be an additional safeguard, depending on the decision. |
| CC-WORST | “We want to select the classifier that maximizes the minimum correct-classification rate over the 16 identity-mention × toxicity-label groups on this test set.” | Worst-group accuracy directly matches the stated rule. It remains specific to this dataset and its groups. |
| CC-FP-MENTION | “We want evidence that the new classifier reduces erroneous removals of benign comments mentioning each identity, compared with a baseline.” | Report per-identity false-positive rates (or true-negative rates), comparison with the baseline, threshold and uncertainty. Worst-group accuracy is related because it includes these true-negative groups, but a higher aggregate minimum does not establish an improvement for every individual identity. |
| CC-FP-AUTHOR | “We want evidence that the new classifier reduces erroneous removals of benign comments *written by members* of each demographic group on our platform.” | Neither supplied leaderboard metric is sufficient. Need author-demographic labels (where appropriate and lawful), relevant deployment or held-out data, per-group false-positive rates, thresholds and uncertainty. Mention flags cannot substitute for author demographics. CivilComments may be offered as partial evidence about *mentions* if clearly qualified. |

For CC-FP-MENTION, a higher worst-group score improves the reported minimum over the 16 rates, but does not identify which rates changed or prove a decrease in false positives for every identity. For CC-FP-AUTHOR, the population itself differs from the benchmark's measured groups.

**Pilot comparison:** Use the baseline prompt above, then an otherwise identical structured version that asks the assistant to check the claim, target population, groups, error type, metric and inference before recommending. Give both conditions the same evidence and output fields. If changing prompt length appears consequential, use a neutral addition in the baseline. Save model/version/settings, time, complete prompt and unedited response. Rate any unqualified sufficiency claim against the audit key, then have another reviewer check the case before using it as a scored item.

## Reproducible run sheet

The [pilot runner](../../scripts/run_civilcomments_pilot.py) generates the exact 16 prompts (four variants × two conditions × two model configurations), randomizes request order with a recorded seed, and saves each complete prompt, model metadata, raw response or error, and timestamp as JSONL. Each model request is a fresh stateless call with no tools. The answer key in this file is not supplied to models.

```bash
python3 scripts/run_civilcomments_pilot.py --models MODEL_A MODEL_B --dry-run --output pilot_manifest.jsonl
python3 scripts/run_civilcomments_pilot.py --models MODEL_A MODEL_B --output pilot_responses.jsonl
```

The second command requires `OPENAI_API_KEY` in the environment and uses the OpenAI Responses API by default. An alternative compatible Responses endpoint may be passed with `--endpoint`; compatibility must be verified separately. Do not commit keys. The runner was checked locally in dry-run mode: 16 distinct prompts, balanced across all variants and conditions, identical shared evidence, and no explicit author-identity answer in the prompts. **No live API request was made in the preparation environment.** A live run must be checked for errors and reviewed blind before drawing conclusions.

## What this audit establishes and does not establish

This audit establishes a concrete, sourced mismatch to test: *mentions versus authors*, and a subtler *worst-group summary versus per-group false-positive changes*. The published score table supplies a conditional decision reversal for the two stated rules. **It does not yet establish a failure by an AI assistant.** The first [fresh-context recommendation pilot](civilcomments-agents-20261112.md) is now complete: its agents distinguished all four claims, and both blinded agent reviewers found no unsupported recommendations in 16 responses. Reserve independent source cases and further interfaces for the main sprint analysis.
