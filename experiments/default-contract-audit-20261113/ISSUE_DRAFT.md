# Draft: default generative MCQ contracts can misbind labels, choices and prompt fields

Not submitted. Evidence pertains to One-Eval commit `8aba20ad17ee2c7d2391162ac03ffaebcbb17506` and the `open-dataflow==1.0.10` wheel pinned in its lock file. The gallery marks the inspected contracts `reference_mapped`, with `smoke_passed=false` and a warning that golden cases are unverified. These limitations are acknowledged here.

## Reproductions

1. WinoGrande labelled validation diagnostic: raw labels `"1"` and `"2"` both normalize to `B` under the gallery `choice_letter` parser. For 1,267 public validation rows, a source-gold oracle scores 639/1267 while `<answer>B</answer>` on every row scores 1.0. The gallery default selects the unlabelled test split instead; its 1,767 blank labels give `scored_samples=0`, but the public metrics stage returns a primary score of0.0. Validation is an explicitly documented split override in this evidence.
2. SciQ default test: preprocessing places `correct_answer` first in `merged_choices` for all1,000 rows. A constant `<answer>A</answer>` scores994/997 after3 numeric-text references are excluded and3 are misinterpreted as indices. After a balanced semantic option permutation with aligned typed references, the constant scores0.25 while the oracle remains1.0.
3. LAB-Bench default CloningScenarios: the configured choice column is `distractors`; `ideal` is omitted from all33 displayed choice sets. A constantA predictor chooses an incorrect distractor in every row yet scores1.0 over1 scored row, with32 invalid references excluded. This is reproduced through the unmodified public `run_metrics.run_metrics` function, including Step3 output.
4. BoolQ/PubMedQA: literal values `true/false` and `yes/no/maybe` are treated as dataframe column names. Native preprocessing leaves missing choice fields; the locked generator returns before calling the serving backend. Zero-score fixture replays are not represented here as successful end-to-end evaluations.
5. Prompt rendering in the locked API-generation path: the One-Eval normalizer converts placeholders to double braces while the locked formatter performs literal single-brace replacement. The generator passes generic `question/context/choices` fields, but some gallery templates use source-specific `sentence/ctx/support` fields. WinoGrande/HellaSwag prompts retain unresolved question placeholders; changing the source question leaves the generated prompt byte-identical. SciQ's nonempty support fields are similarly omitted. MedMCQA's question field passes the dependency control.

## Checks

These are isolated original-method replays, not a claim that prior published model runs are affected. Constructed controls and prospective real model outputs are labelled separately. The model experiment renders the intended template directly and tests the scorer layer; native formatter failures are tested separately without model calls.

Potential correction: explicit per-source reference semantics and choice literals; validation of gold availability and correct-choice inclusion before inference; canonical reference labels that avoid text/index ambiguity; option permutation for generated-letter evaluations; source-field binding verified by input mutation tests; and a hard failure for an empty scoring denominator. Proposed adapters and causal regression results accompany the report.
