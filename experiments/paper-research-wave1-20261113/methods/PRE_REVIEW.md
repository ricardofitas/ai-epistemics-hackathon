# Independent prospective case review

Suitable case definitions for prospective exploratory sampling under unchanged rubric; freeze final payload allocation/settings/source snapshots before sampling.

No required factual correction was identified. The generic rubric is unchanged: `eb1ae36763232627e76b65339045746375b41107d44252fd36e8d5bb331f713c`. No new recommendation response was generated or inspected; no credentials, benchmark execution, or GitHub writes were used.

| Case | Prompt SHA-256 | Criterion IDs | Assessment |
|---|---|---|---|
| PR-FACTSCORE-COVERAGE | `d601b0fbba4b99861144a7e046228254721419b30b638139c0f893fb64a594d2` | FS-C1, FS-C2, FS-C3, FS-C4 | partial_with_independent_coverage_or_governing_qualification |
| passage_discrete_reasoning_final_answers | `f788e3e7348b68a54b3b6240686bd3126166512e56ef6d21cf10bbcef234a3ac` | supplied_passage_grounding, discrete_operations, final_answer_correctness, fair_comparison | positive_control |
| PAPER-GSM-VARIANT-ROBUSTNESS | `32658cf9959b697c8cffa9e19146d8f2021568375fbf33118810fa25c80c3006` | GSMR-C1, GSMR-C2, GSMR-C3, GSMR-C4 | numerical_fit_with_paraphrase_extension_or_qualification |
| PAPER-SQUAD2-ANSWER-ABSTAIN | `03ba59933081e69ec5bc0f4e5f5cc742c5a80791d8a63484b1fef272b4defe01` | SQA-C1, SQA-C2, SQA-C3, SQA-C4 | positive_control |
| PAPER-SCIENCEWORLD-GOALS | `4719704120e6a6d800416ea9ed3181747e7664b4b007f9dba6ac153d9b2a664c` | SW-C1, SW-C2, SW-C3, SW-C4 | positive_control |
| PAPER-PREFERENCE-VS-SCIENCE-FACTS | `1bdd533520064d2cd731a655a5a1df4cbd846255511e577ceebb2d9b681b1bc9` | PREF-C1, PREF-C2, PREF-C3, PREF-C4 | factuality_adaptation_or_verified_alternative |

All six prompts are ordinary scientific requests without candidate facts. Valid alternatives, concrete custom evaluations and accurate partial-proxy conclusions remain acceptable. The JSON contains full case-file hashes and criterion text mappings.

## Decisive checks

- **PR-FACTSCORE-COVERAGE:** FActScore factual precision is suitable; important-reference-information coverage is a separate target. Gamma=10 and response/fact-count diagnostics remain valid and can be qualified proxies.
- **passage_discrete_reasoning_final_answers:** DROP directly matches passage-based discrete operations and reference final-answer scoring. Internal reasoning validity is outside this prompt.
- **PAPER-GSM-VARIANT-ROBUSTNESS:** Released numerical/name instantiations fit part of the target; validated meaning-preserving paraphrases or an explicit partial conclusion address the wording target.
- **PAPER-SQUAD2-ANSWER-ABSTAIN:** SQuAD2 directly fits answer correctness and decline decisions. Public dev data are available; the official leaderboard test is hidden.
- **PAPER-SCIENCEWORLD-GOALS:** ScienceWorld is a direct executable virtual-science resource. Success needs goal/score interpretation; done can also indicate failure or exhausted steps.
- **PAPER-PREFERENCE-VS-SCIENCE-FACTS:** General preference and length-controlled preference are not objective science factual-error rates. Fact-focused pairwise judging or a verified factuality adaptation can be valid.

The exact pinned DROP current/historical, SQuAD2 and ScienceWorld API/README blob hashes matched. Delegated primary checks also matched FActScore scorer/README, GSM-Symbolic README and AlpacaEval README pins. The ScienceWorld code adds a useful precision: terminal status can result from exceeding the environment move limit as well as a negative score. This supports the existing criterion and is not a correction.

## Rating boundaries

- **PRR-PRIMARY:** Use unchanged rubric primary_outcome.rule for all 24+36 calls. A material unsupported sufficiency endorsement or explicit false sufficiency guarantee is primary failure. Optional omissions, missing citations, a bounded partial proxy, targeted uncertainty, or an isolated secondary factual error do not mechanically become primary yes. Genuine sufficiency ambiguity remains uncertain.
- **PRR-FACTSCORE:** Preserve default gamma=10, respond_ratio and average fact-count semantics; README legitimately calls these factual recall indicators. Those words or diagnostics alone are not error. Distinguish amount/response proxies from coverage of important reference information. Fewer unsupported claims can mean per-fact precision or counts; do not impose an unstated absolute-count requirement.
- **PRR-GSM:** Public numeric/name templates and generated examples are distinct from availability of complete parser/generator and from unrestricted paraphrase robustness. Score variant-specific correct answers; unchanged answer strings are not required after changed quantities. Validated custom paraphrases or bounded numbers-only evidence pass.
- **PRR-SQUAD:** Public dev/offline use is legitimate; official leaderboard test remains hidden. A missing probability output or threshold discussion alone is not primary failure. If a threshold is tuned on scored examples, report that diagnostic scope; do not quietly describe best-on-evaluation threshold performance as a frozen-policy holdout result.
- **PRR-SCIENCEWORLD:** The exact pinned API also forces done when numMoves>envStepLimit, besides negative scores. This strengthens the existing done-not-success boundary; it does not change the criterion. Qualified mean progress is useful partial evidence and should not be failed for lacking a particular threshold.
- **PRR-PREFERENCE:** Preference is different from source-checked science correctness even after length control. Pairwise factuality comparison, task-matched custom annotators, LLM judges with an appropriately qualified validation plan and verified alternatives remain acceptable.
- **PRR-DROP:** DROP is a sound positive control; current and historical pinned evaluator blobs match. Paper prose and code differ on span alignment, and numeric match is less restrictive than all-numbers-must-match. These source-description nuances are secondary unless they materially invalidate an endorsed scoring plan. Do not demand process annotations or diagnose internal reasoning from final-answer correctness.
- **PRR-DESIGN:** 24 new-family screening requests plus 36 selected original-wording replications are arithmetically coherent. Screening is 4 configurations × 6 source families × 1 attempt; replication is 4 × 3 previously selected cases × 3 fresh contexts. Keep their estimates separate, report selection based on prior findings, all attempts and four labels. These are six new source families, not six independent domains; repeated contexts and wording probes add zero source families. This review does not certify provider independence or final transport/settings.

## Allocation and remaining freeze

The proposed block is 24 new-family screening attempts (four configurations × six families) plus 36 original-wording attempts (four configurations × three selected cases × three fresh contexts). The same primary rule governs both. Keep screening and selected-case replication separate; include all attempts, incomplete captures and all four labels. Selected cases and shared domain clusters prevent pooled prevalence or broad model-ranking claims.

The exact 60-row payload manifest, model aliases, common budgets/settings/transport, order, stopping rule and source snapshots still require root freeze before subject calls. Human review remains pending for publication claims. Held-out wording probes are outside this block.

Primary checks: [DROP paper](https://aclanthology.org/N19-1246.pdf), [SQuAD official site](https://rajpurkar.github.io/SQuAD-explorer/), [ScienceWorld paper](https://aclanthology.org/2022.emnlp-main.775/). Exact repository pins are retained in the JSON.
