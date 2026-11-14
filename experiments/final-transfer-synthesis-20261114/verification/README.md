# Independent full closeout and SAME24ID replay

PASS: 109,326 checks, zero failures. Reproduce offline from the workspace root:

```bash
python run2055/verification/verify_full.py
```

The script imports only the archived independent numeric validator for transport checks; it does not import producer design, scoring, or analysis modules. It independently reconstructs the full factorial plan and scoring, preserves all unknowns, verifies eight original ZIP hashes and extracted bytes, and authenticates intents, requests, terminal objects, models, status, text, usage, caps, retries and reservations.

3,200 planned and started slots; 3,236 attempts; 36 explicit HTTP429 attempts; 3,180 original terminal objects. Eligible: 3,086. Unknown: 94 incomplete, 11 missing-terminal HTTP200 streams, and 9 HTTP504 records. No unknown-transport retry or fabricated terminal. The original six-wave report and its 14 overly strict missing-terminal failures remain untouched.

All 32 model/dataset/condition score cells, source-paired contrast bounds, pooled bounds, admissible SQuAD winners and conditional clean-TabMWP regrets match the original final reports. choice_none admits Qwen, DeepSeek and GLM, with target regret 4–6, 18–20 and 0–2 pp. free_clear admits GLM only, with regret 0–2 pp. The winner sets overlap.

SAME24ID links the independently selected 24 numeric-control source IDs and all 192 numeric keys to all 384 parent slots: 370 eligible, 14 unknown. The fixed factual endpoint is retained. No numeric secondary adjudication was repeated.

| Model | Parent condition | Planned | Correct | Dummy | Unknown |
|---|---|---:|---:|---:|---:|
| deepseek-v4-flash | choice_clear | 24 | 23 | 0 | 0 |
| deepseek-v4-flash | choice_none | 24 | 4 | 16 | 4 |
| deepseek-v4-flash | free_clear | 24 | 18 | 0 | 0 |
| deepseek-v4-flash | free_none | 24 | 18 | 1 | 0 |
| gemma-4-31b-it | choice_clear | 24 | 24 | 0 | 0 |
| gemma-4-31b-it | choice_none | 24 | 1 | 23 | 0 |
| gemma-4-31b-it | free_clear | 24 | 23 | 0 | 0 |
| gemma-4-31b-it | free_none | 24 | 22 | 1 | 0 |
| glm-5.2 | choice_clear | 24 | 24 | 0 | 0 |
| glm-5.2 | choice_none | 24 | 6 | 8 | 10 |
| glm-5.2 | free_clear | 24 | 24 | 0 | 0 |
| glm-5.2 | free_none | 24 | 23 | 0 | 0 |
| qwen3.8-27b | choice_clear | 24 | 23 | 0 | 0 |
| qwen3.8-27b | choice_none | 24 | 2 | 22 | 0 |
| qwen3.8-27b | free_clear | 24 | 23 | 0 | 0 |
| qwen3.8-27b | free_none | 24 | 22 | 1 | 0 |

All 14 same-ID unknowns occur under choice_none: DeepSeek 4, GLM 10. Each condition contains 96 repeated source/model observations over 24 source questions. These are not 96 independent source questions.

Available-usage provider cost: 2.8084156544160001053966, matching the reported 2.808415654416 within decimal serialization. Uncached rate-card cost: 2.870182884, published rounded to seven decimals as 2.8701829. The published cap table's received field counts HTTP200 attempts, including the 11 missing-terminal streams; it is distinct from the number of terminal objects.

Limits: raw SSE bytes are absent, so stream hashes cannot be independently regenerated. Frozen 200-case identity and request reconstruction were verified; upstream corpus sampling was not rerun. All 94 raw incomplete terminal statuses remain unknown even where the recorded event name is response.completed. No new model calls or network operations were made.

Files: verify_full.py is the reproducible audit; full_closeout_audit.json contains all results and checks; same24_parent_observations.json contains the complete 384-slot linkage; console.json contains its concise execution output. This successful replay supersedes the temporary recovered summary made before inputs were restored.
