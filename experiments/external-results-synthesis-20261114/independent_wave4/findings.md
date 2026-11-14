Independent offline audit: wave4 only

Audited the authenticated wave4 ZIP, SHA256 `7813394e4550d91ff22fa93f6b85e37f643318ba5d422e03c900eeb4d98bd9ef`, using a parameterized copy of the independent wave3 verifier. The original wave3 script and result were preserved. This wave covers source indexes 75–99: 25 sources (12 SQuAD, 13 TabMWP), 400 of the 3,200 planned slots.

The standard-library-only verifier imports no production modules. All 12,823 checks passed, including independently reconstructed requests and schedule order, intent/attempt identities, reservations, terminal byte hashes, returned model and response identities, extracted output text, usage, caps, retries, cooldowns, pacing rules, and section mechanical score counts.

| Measure | Wave4 result |
|---|---:|
| Unique slots / planned | 400 / 400 |
| Attempts | 405 |
| Eligible completed | 385 (96.25%) |
| Incomplete | 15 (3.75%) |
| Final transport/HTTP errors | 0 |
| Explicit HTTP 429 attempts | 5, all retried after explicit rejection |
| Input / output tokens | 84,948 / 193,680 |
| Provider-reported cost | 0.414908990048 credits |
| Uncached rate-based token cost | 0.422982312 credits |
| Conservative charge | 0.442027186 credits |
| Sum of front/back elapsed times | 955.74 seconds |

Front: 64 slots, 64 attempts, 61 completions, three incomplete. Back: 336 slots, 341 attempts, 324 completions, 12 incomplete. Both stopped normally within their 1.6/8.4 credit ceilings.

All 15 incomplete responses have status `incomplete`, reason `max_output_tokens`, and recorded event `response.completed`. They were correctly treated as ineligible. Twelve were in `choice_none`, two in `choice_clear`, and one in `free_clear`. Model counts: Gemma five, Qwen one, DeepSeek one, GLM eight.

Descriptive mechanical endpoint counts for wave4 only:

| Arm | Correct / 100 | Unknown | Dummy choice |
|---|---:|---:|---:|
| free_clear | 80 | 1 | 0 |
| free_none | 83 | 0 | 0 |
| choice_clear | 85 | 2 | 0 |
| choice_none | 17 | 12 | 71 |

Every eligible response had an answer tag; none required final-line fallback. These are exact-match endpoint counts, without human semantic adjudication or whole-study conclusions.

Four-original operational checkpoint

A separate reconciliation reads attempts from the four original wave directories and compares their disjoint 400-slot increments against the production cumulative summary. It records each original ZIP hash, checks cross-wave slot/response identities, and matches counts, tokens, reported cost and rate-card cost. It does not count prior wave checks as new scientific results.

| Original wave | Slots | Attempts | Eligible | Incomplete | HTTP 429 |
|---|---:|---:|---:|---:|---:|
| 1 | 400 | 405 | 389 | 11 | 5 |
| 2 | 400 | 406 | 388 | 12 | 6 |
| 3 | 400 | 407 | 386 | 14 | 7 |
| 4 | 400 | 405 | 385 | 15 | 5 |
| Total available | 1,600 | 1,623 | 1,548 | 52 | 23 |

Cumulative tokens: 339,124 input / 741,771 output. Reported cost: 1.508272907768 credits; uncached rate-card cost: 1.540143692 credits (production rounds to 1.5401437). Waves 5–8 remain pending: source indexes 100–199 and 1,600 slots. Therefore the planned panel has 1,652 unknown endpoints at this checkpoint (52 incomplete and 1,600 unstarted), not a fully completed sample.

Limits: frozen upstream source selection was not rederived. Raw SSE bytes are absent, so recorded stream hashes cannot be independently rehashed; all retained terminal bytes were verified for the newly audited wave. No provider calls, Git writes, Library writes, or new human validation occurred.

Reproduce wave4:

`python run1853/independent_wave4/audit_wave.py --wave 4 --zip-sha256 7813394e4550d91ff22fa93f6b85e37f643318ba5d422e03c900eeb4d98bd9ef`

The verifier also accepts `--run-root`, `--input`, and `--output`. Run `reconcile_checkpoint.py` for the four-original operational reconciliation.
