# Instruction-by-options-carrier diagnostic

Prepared only: **zero model calls**. The package compiles20 questions,2models and4conditions (160 proposed unique requests). It does not contain a live provider executor, credentials or permission to launch. A future launch must use the separately reviewed hardened capture path and satisfy the prerequisites in PROTOCOL.json.

Run `python3 prepare.py` to reproduce source selection and manifest offline, then `python3 verify_offline.py` for coverage/identity/contrast controls. Analyze a future verified scored-record JSONL with `python3 analyze.py scores.jsonl`. A scored row requires trial_id, matching request_sha256, verified_complete=true, and score0or1. Missing rows/null scores retain unknown status. These helpers never call a model.

The selection uses the pinned200record capture (100freeform), excluding the prior20generation cases by source hash **or normalized question/context**. That removes23source rows, revealing repeated normalized question text in the pool; the new20panel is selected from77remaining rows. This is a new generation panel, not unseen project data. Exact normalized exclusion does not detect arbitrary paraphrase overlap or prove a global exposure census.

Only instruction text and the presence of `Options:\nA. None` vary within a source/model. Source question/context, shared task prefix and answer-tag suffix are identical. All4factor combinations are intentional diagnostics; some are malformed by construction. They are not byteexact upstream endpoint reproductions or a benchmark accuracy estimate. Existing binding-only/officialtyped endpoints remain archival references.

The order is deterministically counterbalanced: every condition occupies each within-model serial position5times across20sources; model leads alternate. This controls declared ordering imbalance without randomized population inference. The condition labels encode task instruction and carrier separately. Per-model instruction contrasts at each carrier, carrier contrasts at each instruction and their interaction distinguish the candidate causes on this fixed panel.

Input capture provenance: ricardofitas/ai-epistemics-hackathon@2637c3d18cc9dd5f8005f1f6385dfd6a3862c603, experiments/mixeval-scoring-20261114/input/SELECTED.jsonl.gz, gitblob1232735d070afc7882f481103b5df532f8359c48. Retrieved through connected repository access using base64 file content. Original official source revision66a05ec3821a2b5089ed1e32a5d65ab6ecdbf906; reuse recorded rather than relabeled fresh acquisition.

The proposed caps are160calls,4096outputtokens/request,8192UTF8promptbytes, one attempt/request, sequential and at least5seconds between starts. They are resource caps, not verified available credits or current billing authorization. Preserve incomplete responses and stop on capture/provider/usage integrity failures. Do not retry the prior80call study.
