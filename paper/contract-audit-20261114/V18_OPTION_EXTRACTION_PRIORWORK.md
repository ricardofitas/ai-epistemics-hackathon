# Directed primary-source follow-up

14 November 2026. These references were not present in the initial eight archive/blind source copies. A bounded directed lookup now supplies exact primary records. No manuscript or ledger edits made.

## Molfese: prior extraction study

Francesco Maria Molfese, Luca Moroni, Luca Gioffré, Alessandro Scirè, Simone Conia, and Roberto Navigli. 2025. **Right Answer, Wrong Score: Uncovering the Inconsistencies of LLM Evaluation in Multiple-Choice Question Answering.** Findings of the Association for Computational Linguistics: ACL 2025, pp.18477–18494. DOI:10.18653/v1/2025.findings-acl.950.

Primary record: https://aclanthology.org/2025.findings-acl.950/

Inspected scope: official abstract and bibliographic metadata only. The abstract describes comparing extraction strategies with human judgments, systematic LLM-extractor errors, and a tension between answer-format constraints and reasoning. This directly rules out presenting generic extraction sensitivity as a new discovery. It does not establish whether the paper already studies this exact TabMWP default; exact-mechanism novelty remains unreviewed.

Suggested acknowledgment: “Molfese et al. [17] already compare MCQA answer-extraction methods against human judgments and document systematic extraction errors and a trade-off between output constraints and reasoning; our TabMWP contribution is the pinned historical replay and its quantified scoring-policy consequences.”

## Zheng: downstream official-script use

Mingyu Zheng, Hao Yang, Wenbin Jiang, Zheng Lin, Yajuan Lyu, Qiaoqiao She, and Weiping Wang. 2023. **Chain-of-Thought Reasoning in Tabular Language Models.** Findings of the Association for Computational Linguistics: EMNLP 2023, pp.11006–11019. DOI:10.18653/v1/2023.findings-emnlp.734.

Primary record: https://aclanthology.org/2023.findings-emnlp.734/

Primary PDF: https://aclanthology.org/2023.findings-emnlp.734.pdf

Inspected scope: abstract/metadata and PDF section4.1, especially printed page11010 (PDF fifth page). The authors explicitly report exact-match scoring using the official evaluation script. This supports downstream-use context, not prior recognition of extraction defects, provenance of the exact executable revision, or a demonstrated effect on TaCo’s results. The checkpoint’s absence-of-output claim was not rechecked here.

Safe optional sentence: “Zheng et al. [18, section4.1] also report use of TabMWP’s official evaluation script; we have not re-scored their outputs or established an effect on their TaCo comparison.”

The new claim ledger should remain bounded to the released Lu et al. baseline files. Do not expand C21 to Zheng/TaCo conclusions from this citation alone. Full prior-art coverage and exact-mechanism novelty remain open.
