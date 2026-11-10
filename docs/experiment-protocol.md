# Experiment protocol

**Status: proposed.** Freeze the case criteria, prompts, scoring rules and analysis choices before the main run. Log any later changes as deviations; use pilot cases separately from the main set.

## 1. Build and verify cases

Each case should include:

| Field | Contents |
| --- | --- |
| Case and source IDs | A stable case ID; link variants to the same underlying source case. |
| Research goal and decision | What claim the researcher wants to support and what choice the result should inform. |
| Available information | Candidate benchmark descriptions and source excerpts, with dates and links. Do not silently give one condition extra evidence. |
| Critical requirements | Pre-defined dataset, metric, population, protocol or evidence requirements, including what a partial proxy cannot establish. |
| Acceptable outcomes | Multiple valid choices or combinations, conditional answers, clarification and no sufficient candidate, where applicable. |
| Decision data | Existing comparable results and a decision rule if a consequence analysis is possible; keep these separate from the recommendation prompt unless the scenario requires them. |
| Provenance and review | Primary sources, curator, independent reviewer, disagreements and resolution. |

Construct cases using primary benchmark papers, documentation and public results. Do not classify a benchmark as unsuitable merely because it was not designed for the exact claim: record what evidence supports the connection and which limitations are material. Document whether no option is sufficient among the supplied choices; do not claim no suitable benchmark exists anywhere.

Include positive controls, partial-fit and no-sufficient-option cases. Use paired versions that change a meaningful objective while holding candidate information fixed. Do not make the intended answer obvious through candidate order or wording. Keep pilot cases separate from the final case set and reserve enough time for source verification.

## 2. Conditions and models

Select at least two available assistants or model configurations and record provider, exact model version, interface/API, settings, date, access to tools and costs. Use a fresh conversation for each response. Begin with the same case text, source excerpts, requested response fields and comparable generation limits in both conditions:

- **Baseline:** request an evaluation recommendation, explanation, limitations and confidence.
- **Structured check:** request the same output, with an explicit check of claim, task, data, metric and the gap between the evidence and conclusion.

Supply identical evidence to the two conditions. Where practical, use a neutral, similarly sized addition in the baseline so the contrast does not merely reflect extra prompt length. The intervention is the checklist, not an extra source or a different model. Rotate candidate order using a recorded seed and balance condition order where possible. Log timeouts, refusals and malformed outputs; do not quietly drop them.

An optional open-ended pilot may let assistants search freely. Report it separately: differences in retrieval, available sources and reasoning cannot then be cleanly separated. The controlled case set is the main comparison.

## 3. Shared response request

Use the same response fields for both conditions:

1. Recommended benchmark(s) and metric(s), if any.
2. The intended claim and decision they address.
3. Why the evidence fits, including source references where available.
4. Important limitations, assumptions or missing information.
5. Whether to proceed, qualify the claim, ask for clarification, add another evaluation, or state that no supplied option is sufficient.
6. Confidence in the recommendation and what would change it.

Do not force a single benchmark when a combination or a qualified answer is appropriate. Record the actual prompts and any model-specific formatting in the run log.

## 4. Scoring rubric

Before seeing model outputs, define critical requirements for each case and at least one acceptable decision. Two reviewers should independently inspect the case definitions; for response ratings, use two blind reviewers where feasible and adjudicate disagreements. Conceal model and condition identifiers where possible, while recognizing that answer wording may reveal the condition.

Mark a response as an **unsupported recommendation** when it recommends an evaluation as sufficient for the stated claim or decision despite missing a pre-specified critical requirement, without an accurate qualification that resolves the mismatch. Cite the exact case requirement and response passage. In unclear cases, mark uncertain and adjudicate rather than forcing a binary label.

Record separately:

- all critical limitations identified, some identified, none identified, or not applicable;
- appropriate clarification or abstention, unnecessary abstention, or failure to abstain when no supplied option is adequate;
- evidence references: supported, unsupported, unverifiable, or absent;
- whether a paired objective change led to a defensible change or qualification;
- confidence and any visible overstatement, without treating confidence as calibrated unless calibration can actually be assessed.

Pre-define how incomplete outputs are handled. Report counts of unscorable, failed and excluded calls with reasons; assess whether exclusions differ by condition. Retain non-sensitive original responses for audit.

## 5. Worked decision consequences

For each case with comparable published results, freeze the decision objective and rule before evaluating the model response. For example, if the research goal explicitly prioritizes worst-group accuracy, compute which candidate is favored by average accuracy and which by worst-group accuracy. Report the difference in percentage points, source, protocol and relevant uncertainty. Compare like with like and do not mix scores from different datasets as though they had a common scale.

Present this as: **if a researcher followed this recommendation under these stated assumptions, the selected method would be X rather than Y**. It is a retrospective scenario, not evidence of actual adoption, real-world outcomes or a causal harm.

## 6. Analysis and reporting

- Report the primary rate with numerator, denominator and counts by model and condition; give the number of distinct source cases and variants.
- Compare conditions on matched cases. Report the direction and magnitude of differences and uncertainty, rather than relying only on a significance test.
- If bootstrapping, resample at the independent source-case level, keeping paired variants, conditions and repeats together. With very few cases, intervals will be wide or unstable; present case-level results and avoid broad prevalence claims.
- Report positive controls, qualified recommendations, appropriate abstentions and disagreement rates. Show examples of both successful and unsuccessful advice.
- Separate exploratory findings, pilot results, pre-specified analyses and deviations. If both conditions perform well, report that result without inventing a failure.

## 7. Reproducibility record

For every run retain the case version, prompt, evidence presented, candidate order, random seed if used, model and settings, timestamp, raw response, rating, supporting passage, reviewer and status. Do not store API keys or private data. Follow source licenses and team permissions before adding external datasets or prior project artifacts.
