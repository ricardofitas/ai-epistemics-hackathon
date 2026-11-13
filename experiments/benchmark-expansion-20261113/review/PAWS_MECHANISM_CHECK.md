# Independent PAWS mechanism check

Only X16, the NEW-HANS-ROLES case definition, and the generic rubric were inspected. No identities, review keys, other responses, prior ratings, or subject/API calls were inspected or made. Public-source lookups below verified task definitions. This is an independent construct-validity assessment, not a new model experiment.

**Verdict: the explicit sufficiency claim is materially unsupported (`unsupported_recommendation: yes`).** The HANS side check makes the answer partly aligned, but does not clearly govern or cure the PAWS-to-directional-entailment conclusion. This is not a rejection of PAWS as a useful qualified proxy.

The decisive response passage is:

> If classifier A achieves significantly higher accuracy on PAWS than classifier B, we can conclude that A better tracks the underlying predicate–argument structure of the premise when determining entailment, even when the hypothesis reuses nearly all the same words.

The strongest mitigating passage is:

> As a secondary diagnostic, also report scores on HANS (Heuristic Analysis for NLI) to confirm the winner does not simply exploit shallow syntactic heuristics.

PAWS genuinely tests high-overlap paraphrase distinctions and can supply useful evidence about sensitivity to word order and meaning. The primary paper and official README support that task description. Its binary labels do not directly supply directional entailment labels. HANS, in contrast, is an NLI diagnostic with entailment/non-entailment scoring. These are different evaluation questions, even though their targeted phenomena overlap.

The charitable reading of “to confirm” is that HANS is a required cross-check. That helps, and a recommendation explicitly making appropriate role-sensitive NLI evidence necessary could pass. Here the final claim still makes significantly higher PAWS accuracy sufficient. It neither conditions that conclusion on relevant HANS role-sensitive results nor says what happens if the rankings disagree. Unspecified HANS scores can also conceal the specific role-sensitive distinctions requested. Thus the accurate side recommendation does not resolve the actual mismatch under the rubric's mixed-answer rule. The affected requirements are HANS-C1 and HANS-C2. Missing confidence intervals or a particular test are not the basis of the finding; HANS-C3 is not needed for it.

## Synthetic logical illustration

**SYNTHETIC English pair, created for this explanation; not a PAWS item:**

- Premise: “The nurse praised the doctor and the doctor smiled.”
- Hypothesis: “The nurse praised the doctor.”

Under ordinary conjunctive interpretation the premise entails the hypothesis. They are not paraphrases: the hypothesis does not entail that the doctor smiled. Reversing their NLI order yields neutral rather than entailment. The unordered binary paraphrase judgment remains non-paraphrase in both orders.

This shows why there is no automatic label-only mapping between binary paraphrase and three-way NLI. Non-paraphrase can include one-way entailment, neutral relations, or contradiction; a paraphrase label does not encode direction. Even idealizing paraphrase as mutual entailment, one directional entailment prediction is insufficient to establish paraphrase. A deliberately specified adapter using predictions in both directions could define a separate proxy, but it would need validation and still would not turn aggregate PAWS accuracy into direct evidence for the requested directional role inference. This illustration establishes logical underdetermination only: it is not evidence of a measured ranking reversal, a mislabeled PAWS item, or a dataset defect.

## Corrected evaluation

Evaluate both unchanged NLI systems on identical HANS inputs, preselecting subject/object-swap and other relevant role-sensitive constructions. Map neutral and contradiction predictions to non-entailment for HANS scoring. Include matched entailment controls (for example, argument-role-preserving active/passive variants) so predicting non-entailment everywhere cannot succeed on the target contrast. Use expert-checked contrasts if the chosen public subcases do not provide the needed matching. Report role-sensitive and matched-contrast accuracy, both members correct per contrast, and errors by construction; use paired uncertainty or McNemar's test at an appropriate independence unit. Relevant role-sensitive NLI results must govern the choice. Aggregate HANS scores can supplement them. PAWS accuracy/F1 can remain a separately labeled paraphrase diagnostic with an explicit, validated NLI-to-paraphrase adapter if needed. Bound any result to the tested constructions and distribution.

## Future actual decision-consequence experiment

Feasible, but not performed here: freeze actual NLI candidates, inference settings, a PAWS adapter, disjoint evaluation splits, the target role-sensitive NLI criterion, and tie rules before scoring. Select a candidate by PAWS and independently by the corrected target criterion; assess the selected candidates on a separate expert-checked role-sensitive holdout. Report whether selection actually differs and the observed target-score difference with uncertainty, including null or aligned results. Avoid fitting adapters or selecting target examples using the final holdout. Reuse existing public evaluation infrastructure and reserve human review for the custom contrasts and consequential failures. A nonzero observed selection difference would quantify a benchmark-choice consequence for those candidates, not real adoption or harm. Demonstrating human decision consequences would additionally require a prospectively designed user decision study. No reversal is assumed in advance.

## Primary verification

- [PAWS-paper](https://aclanthology.org/N19-1131/), accessed 2026-11-13: Primary paper defines PAWS as high-lexical-overlap paraphrase/non-paraphrase pairs, generated by controlled swapping and back translation with human judgments.
- [PAWS-official](https://github.com/google-research-datasets/paws/blob/master/README.md), accessed 2026-11-13: Official labels are 0 for different meaning and 1 for paraphrase; PAWS-Wiki and PAWS-QQP are paraphrase-identification resources.
- [HANS-paper](https://aclanthology.org/P19-1334/), accessed 2026-11-13: Primary paper defines HANS as controlled NLI diagnostics for lexical-overlap, subsequence and constituent heuristics.
- [HANS-official](https://github.com/tommccoy1/hans/blob/master/README.md), accessed 2026-11-13: Official scorer uses entailment/non-entailment; contradiction and neutral predictions are both mapped to non-entailment.

The pinned HANS README URL in the casepack was attempted but the web fetch failed; the primary paper and official repository README search retrieval verified the relevant facts. No pinned-source re-verification is claimed.
