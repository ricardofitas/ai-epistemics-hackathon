Historical review preserved from the preceding stage. Its replacement text is now integrated into manuscriptv1.2; statements about unchangedv1.1PDF or pending transfer describe that earlier stage.

# Contribution audit — 14 November 2026

Private addendum to working draft v1.1. This review changes scientific positioning, not experimental results. The unchanged PDF's statement that SANE full text was unavailable is superseded by this addendum.

## Comparison with primary sources

| Work and inspected scope | Established contribution / overlap | Implication for this project |
|---|---|---|
| [SANE v2](https://arxiv.org/html/2610.28886v2), sections1–4,6 | Automates scorer-specific capabilities, recipes and expected score relations. Separates recipe alignment, realized perturbation and relation applicability. Uses generated cases and oracle validation; evaluates judge rankings against human labels. | Generic metamorphic testing, scorer-dependent relations and separating intended from realized tests cannot support a novelty claim here. Our independently sourced task semantics and concrete source-to-request defects are the empirical target. |
| [EvalEng v1](https://arxiv.org/html/2605.24213v1), abstract and section7.1 | Studies evaluation infrastructure and explicitly recommends semantic contracts, oracle-independent scoring verification, metamorphic/differential tests and version-pinned fail-fast checks. | This is closer prior motivation than prompt-sensitivity work. Neither semantic evaluation contracts nor failing before corrupted scores should be presented as new general principles. Our contribution must demonstrate an implemented intervention and measured failure consequences. |
| [Judge Reliability Harness v1](https://arxiv.org/abs/2603.05399v1), abstract only | Generates judge-reliability tests from benchmark data/configuration, covering binary and ordinal assessments and perturbation sensitivity. | Test-suite automation and formatting-sensitivity findings alone are insufficient differentiation. No implementation-level coverage comparison is established from this abstract. |

SANE's full-text route resolved by explicitly selecting v2; the previously attempted v1 route remained inaccessible. This is a bounded primary-method comparison, not an exhaustive novelty search. The distinctions in the final column are our interpretation. No absence-of-feature assertion about these systems follows from the inspected sections.

## Claim decisions

| Proposed claim | Decision | Required wording or evidence |
|---|---|---|
| Evaluation infrastructure can silently change scores | Established motivation | Cite prior infrastructure work; do not claim discovery of the general phenomenon. |
| Semantic contracts and pre-inference fail-fast checks are new | Reject as general novelty | Describe our pinned implementation and its measured trust boundary. |
| Metamorphic test validity needs explicit checking | Established methodology | Keep source validity and expected-relation justification explicit; avoid claiming the principle. |
| Specific One-Eval transformations violate source task semantics | Retain as bounded empirical contribution | Exact source/framework revisions, independent reference reconstruction and actual request evidence. |
| Repair changes model-evaluation conclusions | Retain within existing diagnostic panel | Report incomplete-response bounds and dependency groups; do not claim population prevalence or real-world ranking reversals. |
| The checker generalizes independently | Unsupported | Existing mutations and Harness cases reuse observed sources. Freeze an actually unseen source evaluation first. |
| Better than SANE/JRH/GAMMAF | Unsupported | Different objects, denominators and outcomes; no comparable controlled study performed. |

## Manuscript replacement text for next substantive revision

Prior work already motivates semantic compatibility checks and oracle-independent verification in evaluation infrastructure (Zhao et al., arXiv:2605.24213v1, section7.1). We therefore do not claim novelty for semantic contracts, metamorphic relations, or fail-fast gating in general. Our empirical focus is the pinned chain from official source semantics to effective requests and parsed references, its demonstrated defects, and controlled score consequences. A comparative implementation study and independent unseen-source validation remain open.

The SANE comparison in the table should accompany that paragraph; retain a clear separation between deterministic source-contract auditing and stochastic judge reliability. Source-bound auditing is a focus and evidence choice, not proof that no earlier tool offers overlapping checks.

## Next scientific decision

Prioritize independent validation of the implemented intervention over expanding a known-fault calibration panel. Before observing new outcomes, assemble an exposure ledger across earlier project packages, pin the candidate official corpus revision, freeze checker/adapter hashes and sampling, and commit the protocol. An unseen dataset name alone does not establish unseen examples or independence. No new sample has been selected or evaluated in this iteration.

A healthy-source transfer can test false alerts but cannot establish natural fault sensitivity. Altered cases must be separately labeled as constructed. Retain acquisition errors, unresolved references, overlap and unsupported record types with their denominators. Zero new inference is the initial default. Do not pool source records, synthetic variants, task configurations and option requests as independent observations.

## Upstream correction provenance inspected for v1.7

One-Eval PR63, merged1July2026 (merge9addc1ecd29a30d4e4187f4dfd55142958d641ea), already describes answer-extraction/scoring corrections and a change to primary-metric headline reporting. The exact defects and interventions in this case study require their own attribution. The primary PR establishes prior recognition of scoring/reporting problems. The new bounded public search also inspected DataFlow paper2512.16676v1, section7.1/Table2, where ARC-C and WinoGrande results appear. Their link to the affected implementation and per-question artifacts remains unresolved. Evidence is preserved in evidence/external_followup.json.

## v1.8: directed full-method comparison
Molfese etal2025, Right Answer, Wrong Score, FindingsACL950: sections3.2/4.1/5/6 and AppendixA cover Logprobs,18RegExpatterns,xFinder-Llama/Qwen,human judgments on1000responses,format/reasoning tradeoffs,rationale/final conflicts and task-solving extractors. These general mechanisms are prior art. Inspected datasets:MMLU-Redux/OpenBookQA/ARC-Challenge. Bounded full-PDF/method inspection did not locate TabMWP/PromptPG/first-zero-tie default; it does not establish global novelty. Our bounded distinction is pinned source/request/reference transformation attribution, controlled real prompts, and the particular historical ten-baseline policy sensitivity. Primarymethod receipt:V18_MOLFESE_FULL_METHOD_COMPARISON.md. Zheng2023 section4.1 confirms officialscript use; no reanalysis of their unavailable outputs or affectedTaCo conclusion is claimed.
