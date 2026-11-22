# Campaign conclusions

| Experiment | Outcome | Decision |
| --- | --- | --- |
| ScienceQA archive replay | Exact reproduction of the five outputs. Four reversals and one displayed tie in the source block. | Retain the original, historically scoped comparison. |
| Pythia WinoGrande archive replay | All 2,534 correctness indicators reproduced. The constant-B margin contracted from 160 to 48 of 1,267, and the same model was selected on the disjoint assessment. | Record the stable winner as a negative selection result. |
| Local WinoGrande, three runs | Strict format yielded zero parsed answers. FP16 yielded 75 non-finite Qwen A/B logit pairs. BF16 recovered all scores. The constant-B key gave a +73.44-point paired gain when the official gain was zero. | Record the opposite-direction interaction and numerical diagnosis. Leave the 32 untouched pairs unrun under the frozen gate. |
| HELM MMLU v1.0.0 | Twenty-two descriptive reversals over 231 pairs when choosing a five-subject target. Zero changes from the question join, extractor, or original answer key. No held-out confirmations. | Treat the ordering changes as scope sensitivity. |
| HELM Arabic MadinahQA General | Correcting a documented missing passage raised all 25 model scores by 6.81 to 16.28 points. Nineteen descriptive reversals across 300 model pairs. No held-out confirmations. | Support reporting a context-delivery check. Preserve the cross-release and caching limitations. |

The strongest candidate question is whether checking delivered inputs, key bindings and numerical validity can identify when a model-selection claim needs re-evaluation. The ScienceQA and MadinahQA cases show consequential changes in scores. The independent checks provide limited evidence that these changes reverse a particular model selection reproducibly. Existing work establishes sensitivity to question weights, choice scoring and missing comparisons. This campaign supports a reproducible case study and falls short of a new main-track claim. [Related work and candidate decisions](RELATED-WORK.md)

The strongest reviewer objection is that simple positional preference, subject specialization and genuine changes in task information can explain the descriptive effects, while no reversed rank met the frozen independent item criteria. A next experiment could compare an input-binding and score-validity check with ordinary aggregate regression tests on a blind set of real adapter defects. Freeze which comparisons count as actionable and require rank changes to recur on disjoint, matched items. Measure whether the added checks avoid wrong model choices at a fixed audit cost.

[ScienceQA receipt](receipts/scienceqa-cpu.json) · [Pythia replay](receipts/pythia-wino-replay.json) · [WinoGrande GPU results](WINO-RESULTS.md) · [HELM MMLU report](HELM-RESULTS.md) · [MadinahQA report](CONTEXT-RESULTS.md)
