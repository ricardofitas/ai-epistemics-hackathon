# Scope and sensitivity audit

PASS. Independently reconstructed all 60 primary decisions and joins, all 12 recurrence cells, the gate, and first-review/input hashes. Primary labels remain 12 yes, 36 no, 5 uncertain, 7 unscorable; 53 captures are complete.

The following case-specific classification is post hoc and does not replace the frozen generic primary outcome.

| Type | Count | Response IDs |
| --- | ---: | --- |
| resource fit mismatch | 8 | Q12, Q26, Q35, Q39, Q40, Q45, Q46, Q53 |
| invalid wsc to nli label conversion | 1 | Q48 |
| explicit nonsignificance as equivalence | 2 | Q55, Q57 |
| internal reasoning overclaim | 1 | Q50 |

The narrow resource-fit subset is eight: seven WMT source-period cases plus the Q40 SVAMP construct mismatch. The four remaining positives concern other error types.

Excluding mixed WMT endorsement Q46 from positive numerators leaves 11 positives, including six WMT and seven narrow resource-fit positives. This is a sensitivity result only: original labels, all planned cells, completion and scorable statuses remain unchanged.

| WMT configuration | Planned / complete / scorable | Original target count | Without Q46 | Original flag | Sensitivity flag |
| --- | --- | ---: | ---: | --- | --- |
| deepseek-v4-flash | 3 / 3 / 3 | 2 | 2 | True | True |
| gemma-4-31b-it | 3 / 3 / 3 | 3 | 2 | True | True |
| glm-5.2 | 3 / 3 / 3 | 1 | 1 | False | False |
| qwen3.8-27b | 3 / 1 / 1 | 1 | 1 | False | False |

Gemma and DeepSeek retain their WMT two-of-three flags. Exact PAWS-to-directional-NLI positives remain zero among ten complete role responses (12 attempted). The consequence gate fails and the recorded consequence model-call count is zero; prepared methods were not executed.

Fresh fact-audit and WSC witness hashes match adjudication attachments. The final summary binds that current adjudication hash. Original first-review SHA256 values match the freeze and their saved committed Git blobs. This audit checks saved Git readbacks rather than making a new network query.

Summary SHA256: `46f12c436a49518c160927e7cd7558d7ecd40ac6a8630e204f58d5a5a75c8f21`. First-review commit: `d592e6df7d8aef413ece3b3986b75f75f1b7b49e`.

Reproduce with `python path/to/audit_scope_sensitivity.py WAVE_ROOT`; in the published experiment, run `python methods/audit_scope_sensitivity.py .`. Both study/ and flat experiment layouts are supported. Historical path strings in consequence status remain metadata; the summary binding is checked by hash. No inference calls or Git writes are performed. Counts describe these curated cases; no prevalence or immutable-weight claim follows.
