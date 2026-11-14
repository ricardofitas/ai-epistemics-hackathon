# Molfese full-method comparison

Primary PDF: https://aclanthology.org/2025.findings-acl.950.pdf

Citation: Molfese et al. (2025), *Right Answer, Wrong Score: Uncovering the Inconsistencies of LLM Evaluation in Multiple-Choice Question Answering*, Findings ACL, pp.18477–18494; DOI:10.18653/v1/2025.findings-acl.950. Exact full-author citation is in OPTION_EXTRACTION_PRIORWORK.md.

The 18-page primary PDF was available. Targeted inspection covered methods, experiment selection, relevant results and appendices; screenshots confirmed the method and annotation pages. No raw PDF hash was acquired.

| Inspected location (printed pages) | Established overlap |
|---|---|
| §3.2, pp.18479–18480; A.1, pp.18487–18488 | Logprobs, 18 sequential RegEx patterns, xFinder-Llama and xFinder-Qwen. Unmatched RegEx returns no selection. |
| §3.3, p.18480; A.2, pp.18488–18489 | Four prompting settings. The actual CoT template also requests a final answer format; avoid calling it wholly unconstrained. |
| §4.1, pp.18480–18481 | MMLU-Redux, OpenBookQA and ARC-Challenge. |
| §5 RQ1, p.18481; A.3, pp.18488–18490 | Four human annotators; 1,000 responses; identity/gold hidden; invalid-response category. |
| §5 RQ2–RQ3, pp.18482–18483 | Format/extraction/reasoning trade-off varies with domain. |
| §5 RQ4, p.18484; §6, p.18485 | Conflicting reasoning/final answers; answer extractors can solve rather than extract. |

Full-PDF searches found no TabMWP, PromptPG, similarity or default matches. The inspected methods do not describe the TabMWP all-zero-similarity first-choice mechanism. This bounds comparison with this paper; it does not establish first discovery across the literature or uninspected code.

The present archive's defensible incremental claim remains a pinned historical-output replay with 557 changed flags, zero explicit-only inversions and two residual-abstention inversions. The prospective factorial's conditional interaction remains separate. Neither general extraction sensitivity nor content/final-answer conflict should be introduced as a new phenomenon. Human/model adjudication must retain its differing evidential strength.

Suggested concise acknowledgment: “Molfese et al. [17, §§3–6] already compare extraction strategies with human interpretation and examine format constraints, reasoning/final-answer conflicts and extractors solving rather than extracting. Our archive contribution is the quantified sensitivity of the pinned released TabMWP baselines under declared interpretation policies.”
