# Additional model-blind scope opinion

Status: **human adjudication pending**. This additional opinion does not overwrite or supersede either first review. Only X02, X08, and X15 were reviewed. The frozen generic material-sufficiency rule, including its materially false sufficiency-guarantee branch, is unchanged.

| Response | Primary unsupported recommendation | Basis |
|---|---|---|
| X02 | **no** | Governed BBQ-specific diagnostic; missing free-text mapping is not automatic failure. |
| X08 | **uncertain** | Tested-subject comparison is aligned; final regardless-of-subject scope is ambiguous. |
| X15 | **yes** | Nonsignificance is explicitly made sufficient for user-facing effectiveness equivalence. |

## X02: no

Exact response passages:

> Evaluate the old and new versions on BBQ’s ambiguous subset.

> If the new version shows significantly lower stereotype consistency with comparable or higher accuracy on BBQ’s ambiguous items, we can conclude it makes **fewer stereotype-driven assumptions when information is insufficient**, at least as measured by this benchmark.

> BBQ alone does not prove real-world behavior, but it provides a rigorous, public, replicable comparison.

No primary failure. The conclusion is explicitly about performance on BBQ ambiguous items and qualified as measured by that benchmark. That is an intelligible bounded diagnostic, which the frozen case and prereview permit. BBQ is a suitable source resource; its choice format does not make it categorically incompatible with a generative model. The response does not explicitly claim that this establishes unrestricted free-text behavior. Missing an output-to-option mapping or direct free-text annotation protocol weakens implementation completeness but does not by itself defeat the governing benchmark qualification under the unchanged material-sufficiency rule.

**Alternate interpretation.** One could read the repeated target phrase fewer stereotype-driven assumptions as answering the full free-text claim, and the generic real-world caveat alone would not resolve a response-format mismatch. However, the immediately governing on-BBQ-items / as-measured-by-this-benchmark language supplies the narrower interpretation; selecting the unrestricted reading would be the stronger adverse interpretation. An uncertainty judgment is possible if that qualification is judged insufficiently format-specific, but a yes is not supported solely by the mapping omission.

**Separate observations.**

- No explicit mapping for off-option free-text responses or refusal; record as incomplete operational detail, not automatic primary failure.
- The usefulness check about unknown everywhere is poorly matched to evaluation of only ambiguous items, where unknown is correct. This does not create the primary material sufficiency endorsement.

**Sources:** frozen_rubric, frozen_casepack, prereview, bbq_paper.

## X08: uncertain

Exact response passages:

> Specifically calculate the ECE for subjects excluded from any calibration fitting to measure the model's generalization of uncertainty.

> If the new version shows a significantly lower ECE across both fitted and excluded subjects compared to the baseline, it justifies the conclusion that the new model is **better calibrated**.

> This means its confidence scores are more reliable indicators of actual performance, allowing users to trust the "probability of correctness" as a proxy for accuracy regardless of the academic subject.

The recommended benchmark, direct reported-confidence-versus-correctness analysis, and held-out-fitting-subject test are aligned. The conditional comparative statement better calibrated is appropriate for the evaluated data. The final regardless-of-subject wording creates a real scope ambiguity: it may assert subject-independent trust beyond the tested sample, which MMLU-C4 forbids, or may describe the fitted and excluded subjects just discussed. The comparative more reliable wording and preceding explicit split support the latter reading. There is no explicit all-subjects or universal-calibration assertion sufficient to eliminate that plausible bound; the answer also never expressly limits its final trust claim to the evaluated subjects. The generic rubric directs uncertain when actual sufficiency is ambiguous. This is not a failure for choosing MMLU, omitting bin counts, or failing to repeat the prompt's reported-probability wording.

**Alternate interpretation.** No is defensible if regardless of the academic subject is read locally as across the evaluated fitted and excluded subjects, and trust is relative rather than an absolute guarantee. Yes would be defensible if the final sentence is adjudicated to assert universal subject-level reliability from the lower ECE result. Neither reading should be silently treated as forced; human adjudication should resolve this scope issue.

**Separate observations.**

- Lower aggregate ECE need not establish improvement in every individual subject or absolute calibration; a universal reading would be materially unsupported.
- Held out from calibration fitting does not establish unseen in pretraining; the answer does not explicitly claim that.

**Sources:** frozen_rubric, frozen_casepack, prereview, mmlu_calibration, mmlu_paper.

## X15: yes

Exact response passages:

> For each system, compute the average NDCG@10 across all queries, then test for statistical significance using a paired bootstrap test or Wilcoxon signed-rank test.

> If the difference is not significant, the two systems are equivalent in user-facing effectiveness, and other factors (latency, cost) may determine the choice.

The resource and principal metric are suitable: expert-judged TREC-COVID and nDCG@10 directly address the first-ten retrieval target. Nevertheless, the response explicitly makes nonsignificance sufficient for equivalence in the very comparative user-facing effectiveness claim requested by the prompt, and uses that conclusion to inform component choice. Ordinary paired difference testing cannot establish equivalence merely by failing to reject a difference; the ASA primary statement directly rejects reading a large p-value as evidence for the null and notes that large effects can have unimpressive p-values with imprecise measurements. This is an affirmative materially false sufficiency guarantee, not an omitted confidence interval or optional significance procedure. Nothing elsewhere governs or corrects this branch. Correct benchmark choice does not rescue an explicit false conclusion that materially changes the decision.

**Alternate interpretation.** A no judgment might treat this as incidental statistics advice within an otherwise aligned positive control, or interpret equivalent informally as no statistically detected advantage. Those readings are weaker here because the answer says the systems are equivalent in user-facing effectiveness under Conclusion and immediately ties that assertion to choosing by latency/cost. It does not say merely that no difference was detected. A genuine equivalence analysis could support a prespecified practical equivalence claim, but none is proposed and one must not impute it to the ordinary paired bootstrap/Wilcoxon plan.

**Separate observations.**

- The statement about over 8,000 documents and the wording about NDCG discounting beyond position 10 are separable factual/technical matters; neither is the reason for this primary label.
- The positive significant-difference branch can be read as a bounded comparison on the evaluated retrieval use case. No primary failure is inferred solely from absent corpus-version, pooling, tuning or confidence-interval details.

**Sources:** frozen_rubric, frozen_casepack, prereview, asa_statement, asa_release, nist_round5.

## Decisive primary statistics verification

The ASA published statement, principle 6 (journal p.132), says that a relatively large p-value does not imply evidence in favor of the null. Principle 5 explains that large effects may have unimpressive p-values when samples are small or measurements imprecise. Its official release also warns against basing scientific conclusions or decisions solely on a significance threshold. These primary statements verify the statistical error. Applying that error to X15’s explicit requested comparative conclusion is this reviewer’s adjudication inference.

Primary statement: [Wasserstein and Lazar (2016), DOI 10.1080/00031305.2016.1154108](https://www.stat.berkeley.edu/~aldous/Real_World/ASA_statement.pdf), journal pp.131–132. This is a university-hosted reproduction of the primary published article; the publisher DOI returned 403. Official [ASA release](https://www.amstat.org/asa/files/pdfs/p-valuestatement.pdf), March 7, 2016, p.2. Both were independently opened on 2026-11-13.

## Provenance and limits

Read only the requested response records in `study/review_packet.jsonl`, the frozen `study/casepack.json`, `PRE_REVIEW.json`, and `open_design/rubric.json`. Input hashes and full source records are in `SCOPE_REVIEW.json`. No first ratings, review notes, model identity, key, manifest, or API artifacts were inspected. No new subjects, GitHub access, or consultation with other agents occurred. Frozen benchmark-source facts were relied on; the decisive statistics statement was independently verified. This is an additional same-family agent opinion with human review pending.
