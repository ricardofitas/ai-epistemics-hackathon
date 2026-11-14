Independent offline audit: wave3 only

Scope: the authenticated wave3 ZIP with SHA256 `4b1a5fc8a3088aa4b4eb6978b4af3e453f555014eb3f0054970936708c2d0c13`; 400 of the 3,200 planned main-campaign slots, source indexes 50–74. This contains 25 sources (13 SQuAD, 12 TabMWP). It is a partial artifact, not a completed study or a human validation exercise.

The standalone standard-library script imports no production design, scoring, or aggregation modules. It independently reconstructs all request payloads and hashes, the model/arm Latin rotation, first-dispatch order, intent/attempt identities and reservations; verifies all 400 terminal byte hashes, text hashes, model and response identities, usage, caps, status and eligibility; checks all seven retries follow explicit HTTP 429 and recorded cooldowns; checks pacing transitions and recomputes costs. Independently extracted/normalized exact-match score counts agree with each section summary. It completes with 12,841 checks and zero failures.

| Measure | Wave3 result |
|---|---:|
| Unique slots started / planned | 400 / 400 |
| Attempts | 407 |
| Eligible completed | 386 (96.5%) |
| Incomplete | 14 (3.5%) |
| Final HTTP/transport errors | 0 |
| Explicit HTTP 429 attempts | 7, all subsequently retried |
| Input / output tokens | 82,724 / 183,129 |
| Provider-reported token cost | 0.358664940384 credits |
| Uncached rate-based token cost | 0.366560054 credits |
| Conservative charged/reserved cost | 0.423437271 credits |
| Sum of front/back elapsed times | 1,015.45 seconds |

Front: 64 slots, 66 attempts, 61 completed, three incomplete. Back: 336 slots, 341 attempts, 325 completed, 11 incomplete. Both stopped normally and remained within their separate 1.6/8.4 credit ceilings.

All 14 incomplete responses have terminal status `incomplete` and reason `max_output_tokens`, despite the recorded SSE event being `response.completed`. The runner correctly kept every one ineligible. Twelve were in `choice_none`; one each in `free_clear` and `free_none`. The model counts are Gemma three, Qwen three, DeepSeek three, GLM five.

Descriptive endpoint counts for this partial wave only:

| Arm | Correct / 100 | Unknown | Dummy choice |
|---|---:|---:|---:|
| free_clear | 77 | 1 | 0 |
| free_none | 84 | 1 | 2 |
| choice_clear | 91 | 0 | 0 |
| choice_none | 14 | 12 | 73 |

Every eligible answer had an answer tag; none required the final-line fallback. These are the preregistered mechanical exact-match scores, not semantic or human adjudication. Whole-study effects and decisions await the remaining main-campaign artifacts.

Limits: this audit uses the freshly fetched frozen `cases.json` rather than rederiving source selection from upstream corpus blobs. The stored terminal JSON bytes permit independent terminal verification. Raw SSE bytes are absent, so recorded `stream_sha` cannot be independently rehashed. No provider calls, Git writes, or Library writes were performed.
