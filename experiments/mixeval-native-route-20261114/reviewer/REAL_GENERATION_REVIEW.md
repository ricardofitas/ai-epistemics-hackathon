Independent real-generation audit passed.

| Model | Condition | Planned | Completed | Unknown | Correct among completed |
|---|---|---:|---:|---:|---:|
| gemma-4-31b-it | binding_only | 20 | 18 | 2 | 11 |
| qwen3.8-27b | binding_only | 20 | 18 | 2 | 2 |
| gemma-4-31b-it | official_typed | 20 | 16 | 4 | 12 |
| qwen3.8-27b | official_typed | 20 | 17 | 3 | 14 |

Fixed 20-question paired gain bounds are -5 to +25 percentage points for Gemma and +50 to +75 points for Qwen. These are unknown-outcome sensitivity bounds on the observed panel, not population confidence intervals. Complete pairs are 14 and 15, respectively. Both models use the same pinned official optional-rule scorer. There were no new judge calls.

All 80 planned trials have one intent, one recorded attempt and one artifact. Requested and returned model identifiers match exactly. All 80 usage records reconcile to 8,062 input and 66,304 output tokens. The minimum observed start interval is 5.000076 seconds. Cost is 0.057821010000000003215 provider units. Currency is unspecified.

All 11 unknown outputs reach 4,096 tokens and report response.status=incomplete with reason max_output_tokens. Their SSE event type is nevertheless response.completed, as for all 80 trials. Status-aware capture correctly preserves them as unknown, including five Qwen records with no final text. Partial text is never substituted as a completed primary answer.

The intervention restores official task formatting and instructions with identical source questions and legitimate context, under a fixed non-counterbalanced order. The 20 known questions are repeated across two models. They are not 40 independent cases. Source-family exposure and optional-rule scoring limitations remain. The evidence does not establish default model-judge accuracy, full benchmark performance or an independently affected external conclusion.
