# Independent semantic review of the WSC consequence design

**Status: conditionally feasible; no item-level NLI gold is approved by this design review. No candidate calls or predictions were examined.**

The primary SuperGLUE paper (§3.2) defines WSC as a binary pronoun–candidate coreference judgment. Its discussion of WNLI does not create universal three-way NLI labels for full substituted passages. [Primary paper](https://arxiv.org/pdf/1905.00537).

The authentic Mark/Pete witness refutes the universal non-gold→contradiction rule. However, source false does not automatically establish nonentailment of every whole-sentence replacement either: reference identity and propositional truth conditions differ. Each primary conversion needs model-blind semantic validation, preserving source gold separately from analyst-created NLI judgments.

An unresolved-pronoun premise still depends on contextual/common-sense interpretation. Keep it for a faithful-advice arm with explicit conventions and uncertainty flags. A gold-resolved premise is useful as a separate semantic control, but changes the literal task and makes the positive replacement an identity-like entailment. Changing both inputs and scoring is not a scoring-only causal intervention.

Before scoring, validate marked spans, grammar/morphology, quantifier/negation scope and both positive/negative relations; remove or flag genuinely uncertain cases using frozen rules before candidate outputs. A nominative-only filter is a defensible prospective grammar restriction. Group duplicate passages and identifiable schema families before selection/confirmation; source rows are not independent passages.

## Minimal decisive comparison

Hold exact model predictions fixed. Apply the literal bad rule (positive=entailment, negative=contradiction; neutral wrong) and an independently justified repaired binary rule (positive=entailment, validated negative=nonentailment). Require both replacements correct for the passage-pair score, with per-pair accuracy secondary. Keep original source labels and new author judgments separate.

The repaired score cannot be lower merely because neutral becomes acceptable on negatives. Its gain therefore has a mechanical component; a large gain alone is not an impact-level ranking discovery. Preselect candidate configurations, report every candidate and rank/tie outcome, choose strict unique winners on a source-family-separated selection half, and evaluate any distinct choices on the independent repaired-target confirmation half. Preserve nulls and negative confirmation differences. Do not add models or subsets until a reversal appears.

Forty to eighty unique passages can be a useful bounded pilot; schema dependence and semantic validity matter more than the nominal count. Human review remains pending. A changed score rule can establish a conditional scoring consequence on fixed predictions, not general real-world research harm or an intrinsic WSC flaw.

The JSON companion lists seven required design safeguards, the exact semantic-review packet fields and prospective activation requirements. This is a new label-conversion study; it does not reuse or bypass the failed PAWS mechanism gate.
