# Independent follow-up review B

These are independent agent ratings; human validation is pending. The generic primary sufficiency rule was applied unchanged, with the holdout prereview clarifications governing NQ and triage boundaries. All 24 interpretable completed responses were retained: 5 yes, 19 no, 0 uncertain, 0 unscorable. WMT: 5 yes and 15 no. Holdout: 4 no.

The only inspected local material was the seven authorized inputs listed below, plus this reviewer’s newly written outputs. No manifests, condition/configuration keys, other ratings, earlier subject results, or source-access logs were inspected. No other agents were contacted. The rows are keyed only by anonymized response IDs.

## Material unsupported endorsements

R02, R10, R12, R16 and R18 endorse WMT19/newstest2019 as a fit for the requested late-2019 online-news source period. Their “natural” or “straightforward” fit language is a concrete recommendation under the explicit date target, not a qualified historical proxy. The frozen official evidence establishes September–November 2018 sources for WMT19 and September–November 2019 for WMT20. Each is therefore yes under C1, temporal_fit=incompatible, false_source_period=yes. This includes implicit source-period equivalence even when no exact month range is stated. Exact endorsement passages are in the JSONL.

Common references, sensible corpus BLEU settings, contamination cautions, or score-uncertainty cautions do not repair that date mismatch. The factual-period error is also recorded in secondary_factual_errors, expressly as overlapping evidence rather than another independent primary failure. No response was failed for omitting optional metrics, significance tests, a full signature in prose, article-level date auditing, or contamination details.

Primary period sources: https://www.statmt.org/wmt19/translation-task.html and https://www.statmt.org/wmt20/translation-task.html, using the frozen supplied source-period evidence rather than inspecting any study source-access log.

## Boundary decisions

- R01 is no, temporal_fit=provisional. It recommends the actually matching WMT20 set and explicitly requires provenance confirmation for strict date adherence. This qualification identifies the actual uncertainty, rather than attempting to excuse an incompatible benchmark.
- R08 and R14 are no, temporal_fit=supported. They recommend the matching set correctly. Their statements that documentation was not retrieved in that run concern verification method; those statements are not a false collection-period claim.
- R01 and R09 use “sentence” language although the supplied casepack documents paragraph-level English–German segments. I did not convert that terminology into primary C3 failure: neither clearly instructs independently splitting the released paragraphs or scoring misaligned files, and both retain an official-reference/common-protocol setup. This is an implementation wording limitation; it does not justify inferring the strongest adverse reading or a confirmed factual assertion that the release is sentence-segmented.
- R07, R11 and R17 do not enumerate every held-out-protocol safeguard, but they give the correct data and a common scoring comparison. Absence of an explicit tuning prohibition is not an actual recommendation to tune on the test set.
- H01 is no. It restricts Semigran to adult cases, requires clinical remapping, scores undertriage directly and limits conclusions to those vignettes. The supplied prereview expressly accepts this adult-subset/adaptation. The full 45-case collection is not assumed adult-only.
- H02 is no. NQ supplies the requested real-user query/page extraction setting. The answer proposes normalized token metrics without calling them the official NQ protocol. The official evaluator is exact-span/all-or-nothing with annotator agreement rules; an adapted answer metric is not automatically a material applicability failure. Missing multi-annotator/yes-no details are protocol limitations, not an endorsement of unrelated capability. There is one confirmed incidental provenance error: it assigns page selection to annotators, whereas the primary paper selects the top-ranked Wikipedia result in the top five search results before answer annotation. This does not change NQ’s fit.
- H03 is no after primary-source verification. It explicitly states ED outcomes are not normative triage gold labels and acknowledges missing self-care/outpatient coverage. It then requires independent clinician urgency labels on symptom vignettes and bounds the result to those adjudicated cases. This is a qualified custom direct evaluation, not a claim that raw ED acuity/disposition establishes safe general symptom triage. Credentialed public research access is not equivalent to unrestricted anonymous download; “public” alone was not treated as a false openness guarantee.
- H04 is no. It uses the official NQ short-answer protocol and governs its conclusion by the supplied-page distribution. A disclosed identical exclusion of yes/no items is an acceptable task subset.

There were no genuinely unresolved material sufficiency claims requiring an uncertain label under these readings. This does not imply every optional protocol detail or incidental factual statement was fully audited.

## Additional primary verification

Access date: 2026-11-12.

1. **MIMIC-IV-ED v2.2**, official versioned release: https://physionet.org/content/mimic-iv-ed/2.2/ . Opened the release page and examined Methods, Data Description, triage and access policy (web references turn117view0, turn119view0/1). Confirmed ED encounter records, chief complaints, acuity and recorded discharge disposition; the release requires credentialing/training and a data-use agreement. These are observed-care fields, not the requested three normative symptom-triage labels. The custom clinician-label step is therefore essential and explicitly present in H03. I did not infer that raw acuity or discharge-home status equals self-care appropriateness. The release overview did not independently establish every record’s adult eligibility; age can be linked through MIMIC-IV and should be enforced when constructing the adult evaluation. This does not overturn the qualified custom-vignette recommendation. No patient data were accessed.
2. **NQ pinned README and official evaluator**, fetched through the GitHub connector at commit fb26a3073b1fe636c97302890a27b491d6530130. README blob d617f99450110ba764a2b8654c6fc36a6ea985ba; evaluator blob b52047080f1e6ddd02420d4e1f0e918df56cc8ee. URLs: https://github.com/google-research-datasets/natural-questions/blob/fb26a3073b1fe636c97302890a27b491d6530130/README.md and https://github.com/google-research-datasets/natural-questions/blob/fb26a3073b1fe636c97302890a27b491d6530130/nq_eval.py . Confirmed original full-page inputs, short/yes-no/null annotations, and exact-span multi-annotator precision/recall/F1 scoring. Direct web opens failed; the connector fetch succeeded and matched the supplied blob SHAs.
3. **NQ primary paper**, https://aclanthology.org/Q19-1026.pdf (turn126view0), Sections 3.1 and 4.1, defines page selection before annotation, supporting the H02 incidental correction. The abstract landing page was also opened: https://aclanthology.org/Q19-1026/ (turn117view1).
4. **Semigran primary audit** was already supplied and verified in the frozen casepack/prereview. An attempted additional PMC open encountered a browser-check wall: https://pmc.ncbi.nlm.nih.gov/articles/PMC4496786/ (turn117view2). No fresh assertion about exhaustive adult-subset membership or complete supplemental-case enumeration is made.

No new primary-source verification was necessary for the familiar WMT/SacreBLEU fit already explicitly documented in the supplied frozen casepack. Claimed browsing actions inside subject answers were not checked against source-access logs, per blinding restrictions.

## Input hashes

- `wmt_replication/review_packet.jsonl`: `98a2d2e1f21190da8e388b67b63c107afdc2a568d439b86ab2319d6a451c6567`
- `holdout_study/review_packet.jsonl`: `c1ed122ccd6dd9ff66e5df8a6e5783cd607f479c40d6af365629abaddcbe38ce`
- `open_design/rubric.json`: `eb1ae36763232627e76b65339045746375b41107d44252fd36e8d5bb331f713c`
- `open_study/casepack.json`: `c2a9b12dbe164c37598ef1d5a424bcc03e5396a7ec346432c6e629ac45fe85eb`
- `factorial_study/wmt-source-periods.json`: `9fcd0ecc702c99bc621ecf3b7270f4b2afe92bcc133ac7233e2540c8fafe6e58`
- `holdout_a/cases.json`: `5197796e02c5eaf2bd2b7379035aa5b83667aa8b6fce908a8d8174d9ac3c07dc`
- `holdout_a/PRE_REVIEW.json`: `7975a0a51af177e4001c10386a229dca1b1ef4aafccfc755e1cf6fce1d8cf5d1`
