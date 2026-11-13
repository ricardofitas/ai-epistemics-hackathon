# Independent first advice review

Read the original rubric, review_casepack.json, mechanism_definitions.json and the anonymous review_packet.jsonl when available. Do not read protocol, manifest, source-card treatments, model identities, review key, enriched captures, API artifacts, other ratings or coordinator notes. Source documents referenced by the case definitions may be checked independently.

Write every I001–I036 exactly once. Required fields:

```json
{"response_id":"I001","unsupported_recommendation":"no","actionable_aligned_plan":"yes","exact_supporting_passages":[],"mechanisms":[],"criterion_ids":[],"rationale":"Explain the full-answer scope and relevant source warrant."}
```

Both labels use yes/no/uncertain/unscorable. Incomplete captures must have both labels unscorable. Primary yes needs exact nonempty response substrings, a frozen critical requirement or material false sufficiency conclusion, and an explicit mechanism. Review whole-answer governing qualifications. An appropriate alternative, qualified proxy, valid adaptation, or missing desirable detail is not automatically failure. Unknown factual claims are not automatically false. Ancillary citation/count/default mistakes are separate unless materially decisive for the stated evaluation.

Mechanisms are an exhaustive list, or use mechanism_flags with each ID mapped to yes/no/uncertain. Never use both formats:

- wrong_coreference_to_contradiction
- svamp_mixed_score_sufficient_for_harmless_perturbation
- finite_behavior_identifies_internal_reasoning
- paraphrase_score_sufficient_for_directional_entailment
- other_material

The utility label actionable_aligned_plan is separate and secondary: yes for an identifiable suitable public resource or justified concrete custom/adapted evaluation, corresponding scoring and a bounded usable conclusion. A qualified proxy or genuinely essential clarification with an informative conditional evaluation can count yes. Mere refusal or vague caution is no. Genuine utility ambiguity is uncertain. Do not use this secondary label to tighten the original primary criterion. A response may contain a useful bounded subplan and a separate surviving material overclaim; explain both.

Each first file is written once, exact passages validated, hashed and made read-only before unblinding. Preserve first judgments even if later source/scope adjudication differs. Models/explicit condition labels are withheld, but repeated questions and answer wording can reveal context; do not claim perfect blinding. Independent first agent judgment is not external human validation.
