# Round 05 result: Extra search did not improve retrieval triage

Run `retrieval-triage-20261122-r05` evaluated 300 official BEIR SciFact test queries with confidence models trained on 809 official training queries. At exactly 210 accepted queries, the baseline missed 63 top results (30.00%). The model with whole-corpus term-deletion survival missed 64 (30.48%). The reduction was −0.48 percentage points, with a paired 95% query-bootstrap interval of [−0.95, +0.48] points. The standalone top-1-to-10 score gap missed 68 (32.38%). The unfiltered top-1 judged hit rate was 53.33%.

A competitor other than the runner-up displaced the original winner on at least one deletion for 84 queries. That signal changed some decisions yet delivered no measurable gain at the frozen review budget. This is consistent with the strongest simple account: score-distribution features and the runner-up test already capture most useful lexical uncertainty at this coverage. Unjudged relevance and deletion-induced changes to query intent remain alternate explanations. This small study covers one lexical scorer, one review budget and one labeled test collection. The interval quantifies query sampling under the fixed fitted models.

The phase criterion was a verified SciFact result and a gate decision. The expanded method needed at least +3 percentage points and a positive paired lower limit. It failed both. ArguAna outcomes remained unseen, and the formulation was retired. A production team using this exact triage setup has no evidence here for paying for extra competitor scans. These results do not estimate the effect for neural retrievers or contextual variants. [Protocol and primary literature](PROTOCOL.md) · [Run receipt and pinned data](receipt.json)

CPU-only execution. The original BEIR ZIP endpoint timed out and the transport changed to the publisher's commit-pinned mirror before scoring. All raw inputs and per-query measurements stayed outside the scientific branch. The campaign made zero changes to H6, GPU reservations and BOINC mode.

## Replay

Use Python 3.12, NumPy 2.2.6 and PyArrow 20.0.0. From this directory:

```bash
python3 -B fetch.py /path/to/runtime/scifact-hf
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python3 -B run.py \
  /path/to/runtime/scifact-hf /path/to/runtime/retrieval-triage
cmp receipt.json /path/to/runtime/retrieval-triage/receipt.json
```
