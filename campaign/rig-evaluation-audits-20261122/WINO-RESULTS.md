# WinoGrande GPU pilot results

All inference used the RTX 4060 at PCI `00000000:01:00.0` and UUID `GPU-c263bd7e-98ac-501d-3e19-90c15cc3036c`. The models were Qwen/Qwen2.5-0.5B-Instruct at `7ae557604adf67be50417f59c2c2f167def9a775` and HuggingFaceTB/SmolLM2-360M-Instruct at `a10cc1512eabd3dde888204e902eca88bddb4951`. Publisher weight hashes matched. The runner used the same prompts, option order, model snapshots, and 32 question pairs throughout. Every score came from a stored response. Each run discarded its model before releasing the campaign's GPU lock. BOINC continued at always mode during the runs and the campaign made no scheduler or H6 changes.

## First scientific run

Run `wino-rtx4060-20261122-p01` started at 11:22:03 UTC on 22 November 2026 and completed all 64 items and 256 responses at 11:23:30 UTC. The observed shared-load rate was 2,632 fully evaluated items per wall-clock hour over the 87.53-second run, including model loading. Three BOINC tasks were executing on the card at admission and release. This short-batch measurement gives an observed rate under the concurrent load on this card.

All 256 FP16 greedy outputs failed the frozen single-letter parser. The official pair gain and key interaction both scored zero under the zero-credit rule. The corresponding finite-record ranges were −100 to +100 and −200 to +200 percentage points. The zero-credit bootstrap intervals describe the measured scores under the policy and provide no evidence about the answers that could be extracted under a different policy. Observed responses included copies of option lines and punctuation-only strings. The frozen gate excluded the held-out panel. [GPU receipt](receipts/wino-first-gpu.json) · [Scoring receipt](receipts/wino-first-gpu-result.json)

An in-place update to the shell controller caused its post-inference command to exit after the SQLite checkpoint and final GPU receipt had been written. The corrected controller read that completed checkpoint and reproduced the frozen stop decision without rerunning the pilot.

## FP16 forced choice

Run `wino-rtx4060-20261122-p02` evaluated all pilot items with standalone A/B logits. Qwen produced non-finite logits on 11 of 64 full prompts and all 64 omitted prompts. SmolLM2 had finite logits on all prompts. Its full prompts led to 64 B selections, while its omitted prompts led to 48 A and 16 B selections. The official pair gain was zero and the zero-credit interaction was −75 points, with a finite-record range of −137.50 to −15.63 points. The numerical failure motivated the separately frozen precision control. [GPU receipt](receipts/wino-fp16-forced.json) · [Scoring receipt](receipts/wino-fp16-forced-result.json)

## BF16 precision control

Run `wino-rtx4060-20261122-p03` completed all 256 responses with finite logits across both models. It met the technical recovery threshold. The comparison changed arithmetic precision only. This establishes precision sensitivity for the affected checkpoint and inference stack. It does not identify the precise operation that produced the FP16 non-finite values.

| Model | Official full | Official omitted | Constant-B full | Constant-B omitted |
| --- | ---: | ---: | ---: | ---: |
| Qwen2.5-0.5B-Instruct | 0/32 | 0/32 | 32/32 | 10/32 |
| SmolLM2-360M-Instruct | 0/32 | 0/32 | 32/32 | 7/32 |

Each cell counts pairs where both answers received credit. The pooled official gain was 0 percentage points, with a percentile bootstrap interval of [0, 0]. Both models answered 32 of 64 individual questions correctly in each condition. Every pair got identical predictions within each condition. Both checkpoints chose B on every full prompt. The constant-B gain was +73.44 points. The official-minus-constant-B interaction was −73.44 points, with a paired 95% bootstrap interval of [−84.38, −60.94] and an identical-point finite missingness bound because all logits were finite. The frozen positive-direction eligibility gate was unmet. The 32 frozen held-out pairs received zero inference. [GPU receipt](receipts/wino-bf16-forced.json) · [Scoring receipt](receipts/wino-bf16-forced-result.json)

The constant-B key rewarded selection frequency in both precision settings, including when both models tied under the official key. This pilot would change practice by requiring an explicit response-format and numerical preflight, followed by a check that a scored improvement reflects the official key and paired correctness. The closest experimental precedents are the starting manuscript, Alzahrani et al.'s alternate multiple-choice scoring strategies, and Molfese et al.'s answer extraction audit. The strongest alternative explanation is that short-context prompt style and the standalone token scorer favor copying the last option. The evidence covers two small models and one template. A next experiment could distinguish position bias from context use by counterbalancing option order and including a separately frozen passage placebo on stronger local checkpoints. [Alzahrani et al.](https://arxiv.org/abs/2402.01781) · [Molfese et al.](https://aclanthology.org/2025.findings-acl.950/)

Per-item text or logits and timestamps are in the external SQLite ledgers. Their [integrity receipts](receipts/wino-ledger-hashes.json) identify the exact files used for scoring.
