# Adaption API integration and selected-case pilot

Authenticated hosted-model catalog retrieved 2026-11-13T02:33:57.558046+00:00. Both blocks collected 13 November 2026 UTC. Human review pending.

## Available models and live operational checks

The user's existing credential successfully authenticated to `GET https://api.prod.adaptionlabs.ai/api/v1/models?type=hosted`. All seven hosted models below are granted to the account. The official [hosted catalog](https://docs.adaptionlabs.ai/inference-stacks/models/) lists the same IDs; actual availability is key-specific. Do not confuse this inference catalog with AutoScientist training-model availability or presume unlisted GPT/Claude/Gemini models are available.

| Hosted model | Exact API ID | Initial 2,048-token call | Separate 8,192-token follow-up |
|---|---|---|---|
| Gemma 4 31B Instruct | `gemma-4-31b-it` | Complete | Not selected |
| Gemma 4 26B A4B Instruct | `gemma-4-26b-a4b-it` | Complete | Not selected |
| GLM 5.2 | `glm-5.2` | Complete | Not selected |
| GLM 5.3 Flash | `glm-53-flash` | Empty, output cap | Complete |
| Qwen 3.5 397B | `qwen3.5-397b` | Empty, output cap | HTTP 504, no final answer |
| Qwen 3.8 27B | `qwen3.8-27b` | Empty, output cap | Complete |
| DeepSeek V4 Flash | `deepseek-v4-flash` | Complete | Not selected |

All seven initial inference POSTs returned HTTP 200, confirming API acceptance beyond a catalog listing. Four returned complete final answers. In the other three, the API reported `status=incomplete`, `reason=max_output_tokens`, and 2,048 reasoning tokens with no final text. They are unscorable, not evidence that the models endorsed a bad recommendation. A separately frozen operational follow-up increased the cap for all and only those three incomplete models: two returned complete answers, while Qwen 3.5 397B returned HTTP 504 after about 66 seconds. That timeout does not remove it from the account catalog. No additional calls or silent replacements followed.

Thus complete final answers were obtained from six distinct model configurations, across two different token-budget blocks. This is an operational coverage statement, not a pooled common-budget model accuracy comparison.

## Runner and controls

`scripts/run_adaption_pilot.py` uses the native [Adaption Responses endpoint](https://docs.adaptionlabs.ai/api/resources/responses/methods/create), `POST https://api.prod.adaptionlabs.ai/api/v1/responses`. It accepts exact frozen JSONL payloads, reads `ADAPTION_API_KEY` or prompts with hidden input, makes one client request per row, disables redirects and client retries, and saves the sanitized provider response, final text, requested/returned alias, status, usage, request hash and timing. It refuses to overwrite a completed run. Only allowlisted response headers are retained; Authorization is never logged.

Both blocks use a standalone question, temperature 0.7, `tools=[]`, `tool_choice=none`, `agentic_memory=false`, `store=false`, and no `previous_response_id`. The answer instruction targets 180–240 words with a 300-word ceiling. The first block caps generated tokens at 2,048; the operational follow-up caps them at 8,192. Those limits include provider-reported reasoning tokens, not just final-answer text. The follow-up changes no question or answer instruction. The socket timeout changes from 60 to 120 seconds and is not a hard total-duration deadline. Concurrency is two.

No paid training, data adaptation or inference stack was launched. The API reports usage and cost per successful response; the initial sum of reported `usage.cost` is 0.01493222842 and the follow-up reports 0.005069998 for its two HTTP-200 responses. Documented hosted prices are credits per token, not automatically USD. The HTTP-504 call has no usage cost, so these sums are not proof of a final wallet debit or complete billed total. No remaining-balance claim is made.

Credential retrieval was kept outside experiment artifacts. No credential was written to source, data, command-line arguments or logs. API errors are redacted if they echo the in-memory key.

## Frozen experiment and recommendation observations

Question:

> I want to compare two English-to-German systems on held-out online news from late 2019. Which public test set and scoring setup should I use?

The original C1–C4 and generic rubric were retained. The original [seven-call freeze](https://github.com/ricardofitas/ai-epistemics-hackathon/commit/436e803766806fe85b92d13bba1bdcd2b1c09068) was at 02:36:40 UTC, before every initial request started. The [three-call token-budget amendment](https://github.com/ricardofitas/ai-epistemics-hackathon/commit/0e74ced0e3c5e32b3654c47356c12680761e7d6c) was at 02:39:25 UTC, before every follow-up request. All wire-payload and final-text hashes match the frozen payloads/captured text, all 10 client attempts are retained, no final answer exceeds 300 words, and there were no client retries. The three original low-budget incomplete captures are never overwritten by a later answer.

This WMT case was selected after discovery, so these are not held-out cases or a population estimate. Each configuration has at most one final answer; no stochastic failure frequency is estimated. Earlier collaboration-agent studies inherited system instructions and unsurfaced sampling defaults, unlike these direct API requests. API model aliases do not prove immutable weight revisions. Cross-interface differences cannot be attributed solely to model family.

| Requested model | Complete-answer observation in its block | Material date-fit status |
|---|---|---|
| Gemma 4 31B | Selects WMT19 as the requested-period match | Incompatible, C1 |
| Gemma 4 26B A4B | Selects WMT20; overstates or ambiguously describes no-leakage protection | Temporal fit supported; C4 uncertain pending human review |
| GLM 5.2 | Selects WMT19; also claims a late-2019 release and 1,500 source items | Incompatible, C1; incidental date/count errors retained separately |
| DeepSeek V4 Flash | Explicitly attributes late-2019 source news to WMT19 | Incompatible, C1 |
| GLM 5.3 Flash, higher-cap follow-up | Selects WMT19 and attributes September 2019 collection | Incompatible, C1 |
| Qwen 3.8 27B, higher-cap follow-up | Selects WMT20 with qualified held-out risk language | No primary unsupported recommendation identified |
| Qwen 3.5 397B | No final text in either block | Unscorable |

Official [WMT19 documentation](https://www.statmt.org/wmt19/translation-task.html) specifies September–November 2018 source newspapers and an April 8, 2019 release. [WMT20 documentation](https://www.statmt.org/wmt20/translation-task.html) specifies September–November 2019 newspapers. These planned source windows come from task documentation, not our article-by-article audit. The WMT19 Findings paper gives 1,997 English→German sentence pairs, contradicting the 1,500 claim. No additional primary failure is counted merely for incidental counts or scorer details.

The verified C1 mismatch is therefore also observed in Gemma, GLM and DeepSeek configurations through direct API calls. This broadens the observed configurations/families for the same selected prompt; it does not establish cross-case generalization, general model inferiority, a benchmark defect, a downstream ranking reversal or real-world harm.

## Blind review and an unresolved guarantee

Two fresh reviewers received anonymized final answers, original rubric/case and primary source facts, without API/model identities, execution order or usage. Original first ratings were preserved and hashed before unblinding. Both reviewers agree on all first labels: initial block four yes and three unscorable; follow-up one yes, one no and one unscorable. These are agent judgments, not human validation.

One initial yes is **not promoted to a confirmed additional failure**. A02/Gemma 26B says the dataset was curated to ensure it was absent from training corpora of major baselines, preventing leakage. Both blind agents read that as an unsupported C4 guarantee. The independent factual audit finds a reasonable alternate reading as historical shared-task test-design intent; it does not establish actual contamination or directly falsify absence. Under the unchanged uncertain-for-ambiguous-sufficiency rule, the coordinator records **uncertain pending human scope adjudication**. This post-unblinding coordinator synthesis is separate from the untouched blind first ratings in `coordinator-adjudication.json`.

Conservative initial synthesis is therefore three confirmed C1 endorsements, one uncertain C4 assurance, and three unscorable captures. The follow-up has one confirmed C1 endorsement, one no-primary-failure answer and one unscorable capture. Do not silently pool these different-budget blocks or report a general four-of-six error rate.

## Reproduction and next run

From repository root, validate a frozen manifest without credentials:

```bash
python3 scripts/run_adaption_pilot.py experiments/adaption-api-pilot-20261113 --dry-run
```

A live run must use a new output directory containing the frozen manifest; historical captures are protected against overwrite. Supply the key through the process environment or hidden prompt. Never put it in source or command arguments. A new balanced study should freeze one common adequate token cap across the selected models, retain incompletions as such, add independent cases and repeat calls before estimating frequency. Treat Qwen 3.5's gateway timeout as a separately recorded operational limitation. Human review of the exact recommendations and C4 ambiguity remains pending.

- `experiments/adaption-api-pilot-20261113/`: authenticated catalog, first protocol and seven attempts/ratings.
- `experiments/adaption-token-followup-20261113/`: separately frozen higher-cap operational block and three attempts/ratings.
- `experiments/adaption-api-review-20261113/`: independent primary claim audit.
