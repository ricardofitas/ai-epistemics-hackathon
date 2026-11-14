# MixEval: final answer, endorsed content and rule credit

This is a retrospective review of the existing 80-call, 20-question pilot. There were zero new generation or judge API calls. Two assistant reviewers independently examined 69 completed responses with model, condition and previous score hidden; both used the same official question, accepted aliases and response text. Aggregate outcomes had already been exposed, and response formatting can reveal condition. Protocol de205ec97d15cb290815063d4f190279e7410632 was committed before individual adjudication. This is not human validation, the official default model judge, or a prospective independent replication.

The reviewers agreed on 68/69 records for each axis. One perique answer described blending tobacco but did not explicitly state smoking; its final/content correctness remains unknown in consensus. All 11 original incomplete answers also remain unknown. Each model retains 20 paired source questions as denominator.

| Model | Original common-rule score gain | Consensus final-answer gain | Consensus endorsed-content gain |
|---|---:|---:|---:|
| Gemma | -5 to +25 pp | +40 to +75 pp | -35 to 0 pp |
| Qwen | +50 to +75 pp | +55 to +80 pp | +45 to +70 pp |

These are worst-case sensitivity bounds for unknown answers on this fixed, exposed panel. They are not confidence intervals or estimates of a benchmark population effect. The three columns measure different constructs, so the adjudicated columns do not replace the original frozen rule result.

Seventeen responses contain an endorsed correct fact while committing only a non-informative A/None as their final answer: 15 Gemma and two Qwen binding-condition responses. Nine of the Gemma responses receive positive official optional-rule credit from that earlier content. The credited rationale is explicitly factual, rather than an incidental alias match. Thus the observation is a mismatch between whole-text credit and the declared final-answer criterion, not nine proven factual errors or nine arbitrary scorer false positives. Conversely, Qwen's 'Prepare for the worst.' is an unambiguous completion that misses the rule's exact 'But prepare for the worst' alias.

The model difference depends on the measured construct. Within the declared rubric and retained unknown bounds, final-answer repair is positive for both models. The Gemma evidence does not support an increase in endorsed factual content; the Qwen evidence does. Neither result identifies hidden knowledge or general model capability. Instruction and carrier changes remain confounded in the original trial.

Reproduce with `python3 analyze_review.py` after placing the unchanged prior package under `../prior/`. Packet preparation binds the raw request/response/source and frozen analysis hashes. The committed packet and key allow the review aggregation to run independently of that preparation. `INDEPENDENT_VERIFICATION.json` reconstructs all aggregates directly without executing the analyzer.

Next: a fixed, counterbalanced instruction-by-bogus-option diagnostic on new source cases; retain the original panel unchanged. Use source semantic questions/context hashes to document overlap. Do not repeat the completed 80 requests.
