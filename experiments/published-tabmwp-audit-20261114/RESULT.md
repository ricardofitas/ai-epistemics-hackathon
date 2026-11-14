# The released PromptPG advantage survives this natural parser audit

All five original prediction archives at authors' revision 869bae8ffb8288ccc3102293b3090ec2aa17f618 were bound to the 7,686-question test split. Recomputing correctness from each stored prediction and the exact released answer normalizer reproduced all 38,430 stored correctness flags. Questions, raw model replies and source answers were preserved.

In the released seed-2 two-shot CoT files, GPT-3 has 4,882 correct answers and PromptPG has 5,397, a difference of 515/7,686 or 6.7005 percentage points. The comparison uses the same source IDs. The publication's headline mean covers multiple seeds; this release comparison does not reproduce that mean.

| Scoring diagnostic | PromptPG advantage, pp |
|---|---:|
| Released scores | 6.7005 |
| Case-insensitive lexical fallback | 6.7525 |
| Unique whole-option equivalence | 6.7005 |
| Unique equivalence followed by residual zero-tie abstention | 9.0554 |
| Conservative last declared numerical answer | 6.7135 |
| Case-insensitive fallback plus last declared number | 6.7655 |

Thus these tested alternatives preserve the direction of the released main comparison. The baseline-only TAPEX/UnifiedQA sensitivity cannot be used to assert that PromptPG's advantage disappears. Removing residual arbitrary first-option credit particularly affects the GPT-3 CoT baseline, which encountered 402 zero-similarity fallbacks; PromptPG encountered 14.

The released source contains a random option fallback when an extracted letter is outside a question's actual option range. It is invoked 43 times for the CoT baseline and 60 times for PromptPG. Treating every such event adversarially in either direction yields a conservative gain bound of 5.3604–8.0406 percentage points. This alone also preserves the ordering. Non-random extraction paths exactly reproduce the stored predictions for both main-comparison files. The first zero-shot file has six non-random extraction discrepancies and metadata seed 1 despite a seed-2 filename; its stored flags still reproduce from its own stored predictions.

The audit used no model or judge calls. It retains per-item disagreements in changed_items.jsonl and the full counts in summary.json. The next natural source-order audit is a separate hypothesis about adapter-created answer leakage in the current One-Eval gallery. This result is a negative control for the proposed explanation of the released PromptPG advantage.

[Successful original-output replay](https://github.com/ricardofitas/swarm-adaption-hackathon/actions/runs/43641325621).
