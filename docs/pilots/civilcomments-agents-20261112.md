# CivilComments: completed fresh-context recommendation pilot

**Date:** 2026-11-12, pre-sprint exploratory work. **Result:** no unsupported recommendations in 16 completed responses under the recorded rubric. Both independent agent reviewers assigned `no` to all 16 responses, with no primary-label disagreements, uncertain ratings or unscorable responses.

## Design and provenance

The [source audit](civilcomments-claim-fit.md) defines four claim variants: average accuracy, worst-group accuracy, per-identity false removals for identity mentions, and false removals for demographic groups of authors on a platform. We sampled two fresh contexts for each variant in each of two conditions (baseline and added compatibility checklist), for 16 responses. All subjects received the same source evidence and output request. No subject received the answer key or this project's history.

Subjects were instantiated with `collaboration.spawn_agent`, `fork_turns="none"`, no model override, and an instruction to use no tools or delegation. No tool calls were observed. This is one inherited configuration (session-reported `gpt-6.1-sol`), not two models. Exact provider snapshot, generation controls, usage and per-call timestamps were not exposed by this interface. Platform system/developer instructions still apply. Final messages were copied verbatim into the result files with trailing newline normalization.

The complete prompt manifest was committed before sampling at `4fc2accd6a798dfa037cd0c373a7cb0a306337a4`. An independent agent wrote the rubric without seeing outputs; preparation overlapped the first three subject calls, and the rubric was recorded before scoring. This is not a fully preregistered confirmatory study. Two further fresh agents scored an anonymized packet containing case IDs and answer text, without model or condition labels or the review key. Both reviewers use the same model family as the subjects; human review is still needed.

## Results

| Variant | Baseline unsupported | Structured unsupported |
| --- | ---: | ---: |
| Average accuracy | 0/2 | 0/2 |
| Worst-group accuracy | 0/2 | 0/2 |
| False removals by identity mention | 0/2 | 0/2 |
| False removals by author group | 0/2 | 0/2 |
| Total | 0/8 | 0/8 |

The answers selected the matching metric for the two direct selection goals. They requested per-identity benign-comment error comparisons for the mention claim and recognized that identity mentions cannot establish author demographics for the platform claim. The rubric treats optional omissions separately from an unsupported recommendation; neither reviewer identified a primary failure.

These are **four variants of one source case**, not 16 independent scientific cases. The supplied evidence makes relevant distinctions explicit, so success on this pilot does not establish success on open-ended research advice. With no observed errors in either condition, this run provides no evidence that the checklist improves recommendations. The structured condition is also longer, preventing isolation of a checklist-specific effect.

## Reproduction and next research step

All exact prompts, answers, metadata, blinded packet/key, rubric and both rating sets are under [`results/pilots/civilcomments-agents-20261112`](../../results/pilots/civilcomments-agents-20261112). Recompute the summary with:

```bash
python3 scripts/summarize_civilcomments_agents.py results/pilots/civilcomments-agents-20261112
```

This completes the first actual recommendation pilot. The next experiment should use independent source cases and less directive research requests while retaining complete prompt/output provenance, suitable controls, and willingness to report correct recommendations. Numerical evaluation defects, such as the separately reproduced TruthfulQA MC2 stress test, concern implementation validity and must not be counted as observed recommendation errors.
