# One-Eval installed native execution

The installed One-Eval pipeline completed four real requests through its original native HTTP client and native primary metric runner. All four returned complete Qwen responses, with 444 input tokens and 804 output tokens. The minimum observed interval between HTTP request starts was 14.586 seconds. The frozen limits were four calls, one attempt per slot, concurrency one, at least five seconds between starts, 4096 output tokens per call, a 120-second child wall limit and zero judge calls. The independent artifact verifier passed with no errors. [GitHub run](https://github.com/ricardofitas/swarm-adaption-hackathon/actions/runs/43620987144)

This closes the earlier installed-distribution, original HTTP transport and native primary metric execution boundary for these two source cases. Both questions were already exposed. The corrected configuration jointly changes question binding, task route, appended choices, answer convention and a native diagnostic metric. The trial supplies integration evidence on four slots.

| Source index | Configuration | Raw final content | Native primary metric | Interpretation |
|---|---|---|---|---|
| 40 | Original MixEval gallery | `<answer>A</answer>` | Choice accuracy 0, scored samples 0 | Unscorable references |
| 200 | Original MixEval gallery | `<answer>A</answer>` | Choice accuracy 0, scored samples 0 | Unscorable references |
| 40 | Source-typed joint repair | `Dance` | Native normalized exact match 0 | Original HTTP client adds reasoning and answer tags before this metric |
| 200 | Source-typed joint repair | `Tony Blair` | Native normalized exact match 0 | Original HTTP client adds reasoning and answer tags before this metric |

Both original gallery requests contain the unresolved `{{prompt}}` placeholder and the appended `A. None` option. Their native primary metric retains the raw alias-list reference, rejects it as a choice reference and reports zero reference-valid scored samples. The numeric zero is unscorable.

The corrected requests contain the exact source questions. The returned raw factual final contents match accepted source aliases. The original DataFlow API client transforms a response containing `reasoning_content` into `<think>...</think>\n<answer>...</answer>`. Native exact match receives that complete transformed text and gives zero on both corrected responses. DataFlow's earlier `any_math_verify` diagnostic gives one on each. The unchanged scores, raw chat messages and delivered strings are all retained.

Native normalized exact match was explicitly selected as an integration diagnostic for the corrected configuration. The official MixEval model judge remains a distinct endpoint. These two scores document the interaction between the original client formatter and the selected native diagnostic metric.

A post-outcome engineering repair now appends a dedicated `provider_final_content` column copied verbatim from the captured API's `choices[0].message.content`. The typed native metric reads that declared column. Original `generated_ans`, raw native metric results and all source references remain preserved. The mapping validates the original response ID, body hash, request hash and source association before copying the provider-defined field.

The installed native MetricRunner replay completed on all four captured rows. Both typed exact-match scores are now 1.0 with details `[1.0]`. Both original gallery rows remain unscorable with zero scored samples and one invalid reference each. The native exact-match result retains its original `scored_samples` value of `None`; the numeric detail supplies the separately derived per-row eligibility. This replay made zero new provider calls. The four existing real responses remain the complete generation cohort for this integration demonstration. [Installed scoring replay](https://github.com/ricardofitas/swarm-adaption-hackathon/actions/runs/43621794887)

Independent verification passed for both authenticated archives, all four capture/source/benchmark associations, every preserved original column, exact final-content copies, unchanged native metric metadata and installed module hashes. `verify_rescore.py` reproduces the audit without importing the rescore executor.

One-Eval was installed from commit `8aba20ad17ee2c7d2391162ac03ffaebcbb17506`. DataFlow 1.0.10 came from the authenticated wheel with SHA256 `75dd8e03fd96875472c11bd9fdf8af30e66d76a6b2d59b6b426d998db25e8790`. All 250 resolved dependency versions match the earlier successful installation. Seven native module origins and hashes are retained from ordinary site-packages imports. The observation wrapper records and bounds HTTP calls while preserving native request and response processing.

The preceding zero-provider-call fixture run retains its failed workflow conclusion. All four fixture pipelines and metrics completed before an audit assertion rejected pandas' conversion of numeric string IDs to integers. A separate reconciliation and independent review accept only exact string roundtrip equality, preserve both ID values and types, and verify every other source column unchanged. The real protocol incorporated that bounded correction before generation.

The real launch is commit `a29c0a038e9295323fefdddcd412efd01b526995`, with protocol committed at `c31c0619ec0fb7a70332be33a43f43e6dda2ca4f`. Artifact `14124236646` contains 51 ZIP members and has SHA256 `d898dfd28a0d20708b2731a7fbd899d42aadddb5d0a1b2d1617a7c73c3eb47c8`. The frozen independent verifier, original artifacts, dependency receipts and post-run reconciliation support offline reproduction with zero new model calls.

The zero-provider replay protocol was committed at `433db326114f242cd3600b50cb328c67f075a64c` before replay execution, and launched at `dec3c4f0aeb2bd3d3350bbfe18aa3e390e7fc6ce`. The replay is explicitly post-outcome engineering validation with expected results already known. Its artifact `14123944122` contains 20 ZIP members and has SHA256 `63c982408b442dd5771f52a63cdfa492d5446c0e652eab7471d0b4ac0d0b49db`.
