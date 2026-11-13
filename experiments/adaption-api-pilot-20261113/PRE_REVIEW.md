# Independent Adaption pilot prereview

Accepted for a bounded seven-model connectivity and selected-case pilot. No new inference responses were inspected and no API calls were made by this reviewer. This is agent prereview, not human approval.

All seven requested model IDs exactly match the authenticated hosted catalog, with no duplicates or replacements. The unchanged WMT question and common instruction contain no benchmark names, correct answer, or source-period hints. Every payload disables tools, memory and stored conversation history; uses max_output_tokens=2048 and temperature=0.7; and omits previous_response_id. The total requested output bound is 14,336 tokens. The seeded order and frozen input hashes reproduce. The original rubric/casepack hashes match.

The one-attempt rule retains incomplete, empty, unavailable and failed calls. The protocol explicitly withholds broad prevalence, significance, immutable checkpoint identity and model-family attribution across different interfaces. Those limits and pending human review must remain in results.

The runner uses the exact official host with redirects disabled, reads the credential from environment/getpass, redacts it from retained response data, and does not log request Authorization. It preserves complete sanitized responses and separates final assistant text from reasoning/tool items. No actual credentials were read here.

Operational clarification: urllib timeout=60 is a socket-operation timeout, not a guaranteed total 60-second wall-clock deadline. The runner correctly calls it socket_timeout_seconds in its metadata. Clarify this scope in the protocol before freezing and avoid claiming a hard total-duration limit. No prompt or scoring amendment is required.
