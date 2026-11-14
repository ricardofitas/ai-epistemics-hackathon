# Targeted consequence audit: TabMWP
Date: 2026-11-14. Retrospective, post-discovery analysis. Earlier aggregate scores, exact-option witnesses and the first 64-reader workbook are exposed. This is not an independent preregistered discovery.

## Question and scope
Does the evaluator's handling of predictions with zero similarity support a stable comparison between released pretrained TAPEX base and UnifiedQA base?
Connect that result to section 4.2 and Table 3 of Lu et al., ICLR 2023, arXiv:2209.14610v3.
The paper interprets TAPEX performance at comparable model size in terms of tabular pretraining. This audit can assess a component baseline comparison; it cannot attribute a causal pretraining benefit, nor assess the headline PromptPG/GPT-3 comparison without its archived outputs.
Reuse source revision 869bae8ffb8288ccc3102293b3090ec2aa17f618 and the eleven Git blob identities in the existing sources.json. No new model or judge calls. Do not modify manuscript or the existing reader workbook or fill human labels.

## Freeze before raw-output acquisition in this follow-up
Primary pair: results/tapex/exp1_tapex-base.json vs results/t5/exp2_pretrained_unifiedqa_base.json.
Secondary controls: pretrained base/large models at matched sizes; each family's size ordering; fine-tuning comparisons. An equal-weight average over base/large is analyst-defined, not an aggregate statistic attributed to the paper.
1. Reproduce original scores and the previously exposed exact-option and residual-zero scores.
2. Keep zero-similarity residuals separate from uniquely explicit answers after NFKC, casefold and whitespace normalization. A residual is not automatically a semantically wrong mathematical answer.
3. Compute partial-identification bounds when residuals are unknown, and exact counts needed for the pairwise comparison to tie or reverse. For paired bounds, identical normalized residual responses on the same question must receive a shared unknown label.
4. Frozen policies: original first maximizer; unique-normalized-option override only; override plus zero for unresolved zero ties; override plus uniform random residual tie expectation; override plus lexicographic tie. These are policy comparisons, not claims that one is human gold. Nonzero ties and unaffected predictions stay fixed.
5. Deterministic permutation sensitivity: 256 common question-level hash-seeded option orders, shared across models. Generation is frozen; no fresh model/prompt experiment. Report distribution including no inversion; do not choose seeds to obtain a positive finding.
6. Independently reconstruct scoring from raw source, verify Git blob hashes, and check all published aggregate rows. Report any source mismatch and stop rather than substituting a snapshot.
7. Inspect outputs by syntactic category without inferring correctness: direct unique choice; number/currency; other. These diagnostics are post-discovery descriptions.
8. Preserve all policy outcomes. A comparison is robust under unresolved semantic labels only if its entire identified difference interval has one sign. A policy reversal alone is not proof of an incorrect scientific conclusion.
9. Use paired source questions for uncertainty, not repeated model slots as independent units. Finite-archive bounds are primary; optional resampling must be separately labelled.

## Deliverable and decision
A reproducible script, machine-readable results, claim-to-source mapping and a focused report outside the manuscript. Report what a 64-row human reading can and cannot establish. If a robust relevant conclusion change is not demonstrated, explicitly retain that negative outcome and identify the exact missing evidence. No automatic GAMMAF-superiority claim.
