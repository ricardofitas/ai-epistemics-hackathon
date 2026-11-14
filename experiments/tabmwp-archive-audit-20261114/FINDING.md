# The order of published TabMWP baselines is sensitive to how unmatched predictions are scored

We reproduced the test accuracies of all ten released UnifiedQA and TAPEX baselines in Lu et al., ICLR 2023, Table 3; each used the same 7,686 questions. The public score and an independently implemented replay agree on 76,860 archived flags. For all 19,920 multiple-choice outputs (1,992 questions × ten runs), the replay also recovers the original option selected from the raw text. On the 100 free-response questions fixed for the new Adaption study, the independent strict-rational scoring of archived extracted predictions agrees with the released flags in all 1,000 comparisons.

When every candidate has similarity zero, the historical evaluator always chooses the first answer. For pretrained TAPEX base this occurred in 1,238 of 1,992 multiple-choice items; 443 received credit. Item 1529 received credit for Tuesday from the raw text “375” (options Tuesday through Friday). Item 5083 received credit for April from “may”, even though May is explicitly offered. The matcher compares case-sensitively before it selects its first maximizing index. Identifying these cases does not require a new generation.

| Pretrained baseline | Published overall accuracy | Zero-similarity abstention | First-to-last tie-break |
|---|---:|---:|---:|
| UnifiedQA small | 12.18% | 11.90% | 12.11% |
| UnifiedQA base | 14.56% | 14.18% | 14.58% |
| UnifiedQA large | 15.96% | 15.94% | 15.98% |
| TAPEX base | 15.73% | 9.97% | 15.93% |
| TAPEX large | 18.59% | 15.89% | 18.62% |

Giving no credit for all-zero similarity, with all other published scores fixed, reverses three strict comparisons across the ten releases (out of 45 unordered pairs). The strongest example shows TAPEX base originally above UnifiedQA base by 90 correct responses (1.17 percentage points), then below it by 324 (4.22 points). The TAPEX-large versus UnifiedQA-large reversal is only four responses and is fragile. Simply moving the default from first to last changes 901 individual TAPEX-base flags but reverses none of the 45 aggregate orderings. Both alternatives are sensitivity analyses of how a metric should handle unrecognized outputs. The audit does not test the paper’s headline PromptPG vs GPT-3 claim or demonstrate an identical implementation defect in MixEval.

The research question that transfers to the new experiment is whether evaluation format and answer-extraction conventions can determine a model-selection decision. One study re-scores existing outputs and the other changes the actual prompts. The evidence should be reported separately.

Sources and exact numbers: [paper, Table 3](https://arxiv.org/pdf/2209.14610), [authors’ frozen evaluator](https://github.com/lupantech/PromptPG/blob/869bae8ffb8288ccc3102293b3090ec2aa17f618/run_tapex/eval.py), [released predictions](https://github.com/lupantech/PromptPG/tree/869bae8ffb8288ccc3102293b3090ec2aa17f618/results), [successful independent replay](https://github.com/ricardofitas/ai-epistemics-hackathon/actions/runs/43625179457).

## Post-replay check of explicitly stated options

A distinct analysis compared the raw answer with each offered option after Unicode NFKC, case-folding, and whitespace normalization. Among the original zero-similarity rows, 896 raw replies uniquely named an option. Recognizing that explicit option changes 557 historical correctness flags on 432 distinct questions, including 397 gains and 160 losses across the ten runs. The 557 are model-by-question outcomes. The 432 count distinct source IDs. Applying these overrides alone preserves all model orderings. For pretrained TAPEX large it adds 237 net correct answers and moves overall accuracy from 18.59% to 21.68% (3.08 percentage points using unrounded counts).

Recognizing these explicit options and then abstaining only on remaining zero ties preserves two of the three initial strict inversions. TAPEX base moves from 15.73% to 11.11%, UnifiedQA small from 12.18% to 12.01% and UnifiedQA base from 14.56% to 14.23%. The earlier marginal TAPEX-large inversion disappears. The 557 label changes do not depend on abstention. These sensitivities extend the released evaluator and do not re-run the source models. [Replay and per-item witnesses](https://github.com/ricardofitas/ai-epistemics-hackathon/actions/runs/43626394923).
