# Research progress and team review - 14 November 2026

The existing MixEval responses now have a separate, masked content/final-answer audit. No new generation or judge API calls were made. Two assistant reviewers agree on68/69 completed responses; the one disagreement and all11incomplete captures remain unknown. Both the original rule scores and the independent final/content criteria are retained.

| Model | Original rule score gain | Final-answer gain | Endorsed-content gain |
|---|---:|---:|---:|
| Gemma | -5 to+25pp | +40 to+75pp | -35 to0pp |
| Qwen | +50 to+75pp | +55 to+80pp | +45 to+70pp |

Seventeen responses endorse the right fact but end in A/None (15Gemma,2Qwen). Nine Gemma rule credits concern that correct rationale, illustrating different measurement constructs. This is retrospective assistant adjudication on20exposed questions, not a capability result, population confidence interval or human/defaultjudge validation.

Future capture analysis now passes20faultcontrols while reproducing all80originalscores, gains and usage. A derivative49rowmetadata patch separates source/scorerhashes without changing source results. Full installedprovider execution remains open.

## Team repository

Reviewed Antonio's feat/gammaf-epistemic-audit at d4419f160252adee3d639df9ea23cd1600277c32. All11200committedterminal labels replay correctly;227release/delivery discrepancies split156falsecredits/71missedcredits, and1600controls show0. The compactprojection supports terminalreplay;28rawtrajectoryfiles are absent and14fullarchive tests are setupblocked, with19other tests passing.

A reproduced shadow-summary bug mixes combinedcontrol/detectorhits with a detector-only denominator. Correct detectorrate is217/5518=3.93%,control323/1341=24.09%,combined540/6859=7.87%. This correction does not change the227terminaldiscrepancies or alreadycoherentperpopulation rates. An isolated patch with5passingregressiontests is supplied; Antonio'sbranch and frozenartifacts are preserved.

EpistemicGuard results are offline reaggregation of trajectories generated under otherdetectors. The savedsummary does not support superiority over allsixmethods. Shadowevents are observational exposure-associated transitions. These limits should accompany any scientific integration.

Main is still planning-only; team work resides in branches. The Antonio branch has unrelated root history; port focusedchanges to a commonbase after review. The repo snapshot does not establish whether other teammates worked elsewhere.

## Next iteration

A counterbalanced20question x2model x4condition diagnostic is prepared, with160maximumrequests and9passingofflinechecks. It crosses taskinstruction and bogusA.Nonecarrier. The questions are distinct from the priorgenerationpanel under exactsource/normalizedtextchecks but come from an alreadyexposedauditpool. It has not launched: liveexecutor integration/providerpath and final executionrecord remain to be completed. Preserve80requestoldtrial and allunknowns. Continue externalimpact only from newprimarytrace evidence.

Reproduction files are grouped under semantic_review/, hardening/, next_ablation/ and team_review/. The original priorstudy ZIP is retained under inputs/ for exactresponse reconstruction. The updatedmanuscript sources and verification remain separate from the team-review report.
