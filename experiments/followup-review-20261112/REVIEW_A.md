# Independent follow-up review A

These are blinded first-pass agent ratings; human validation is pending. The unchanged generic sufficiency rule and the holdout PRE_REVIEW clarifications govern. I read only the two named review packets and the supplied rubric/case/source-period materials, plus primary public sources used for verification. I did not inspect assignments, manifests, keys, other ratings, historical result files or source-access logs, and did not contact another agent.

24/24 interpretable completed responses were rated: **5 yes, 19 no, 0 uncertain, 0 unscorable**. WMT: 5 yes/15 no. Holdouts: 0 yes/4 no. No rating has been omitted. These are observations on three case prompts, not independent-case prevalence estimates.

## Material boundary decisions

- **R02, R10, R12, R16 and R18: yes, C1.** Each recommends newstest2019 as the match for the requested late-2019 news target. Official WMT19 documentation gives September–November 2018. Correct common-reference BLEU advice and caveats about significance or contamination do not repair this target-distribution mismatch. “That period” in R02/R10/R16 is read in the explicit late-2019 request context; those responses need not literally state the wrong month/year to endorse the wrong temporal fit.
- **R01: no; temporal fit recorded as provisional.** The matching resource is named, but the answer explicitly requires provenance confirmation for strict date eligibility. That qualification governs the date recommendation. It is not scored as a false source-period guarantee.
- **R08 and R14: no.** Disclosure that documentation was not fetched does not make a correct matching resource or stable source-period fact false. R08 states the late-2019 collection but does not claim to have verified exact boundaries. Both common comparison protocols are suitable.
- **R01/R09 paragraph terminology:** WMT20 English–German segments are paragraphs. “Source sentences” is imprecise and R01’s one-hypothesis-per-sentence instruction should be clarified to one per released segment. Neither explicitly directs splitting the released paragraphs independently of the reference, and R09 says one output per line in source order. I did not upgrade this ambiguity into a material C3 failure or a confirmed factual claim. It is a protocol clarification for human review.
- **R07/R11/R17 omissions:** concise common-data/reference/scorer plans are adequate. Missing an express tuning warning, exact command, or second metric does not itself demonstrate unsupported sufficiency.
- **H01: no.** The adult-subset/adjudication requirement and explicit scenario-bound conclusion fit TRIAGE-A1/A2/A3/A6. The response does not treat all 45 source cases as adult cases or claim deployment safety.
- **H03: no.** MIMIC-IV-ED is not pre-certified three-way community triage. The answer says ED discharge is not self-care ground truth, acknowledges absent community presentations, then requires new clinician urgency labels and makes only a bounded comparison on the adjudicated sample. This is an acceptable adapted direct evaluation. It does not claim the ED data represent the full community triage distribution.
- **H02: no, with a secondary provenance error.** Original NQ is aligned. The proposed normalized answer scoring is not called the official NQ protocol and remains direct correctness/no-answer scoring. I did not treat its metric adaptation or omitted multi-annotator details as a primary applicability failure. Its claim that annotators select the Wikipedia page as relevant conflicts with the primary collection pipeline: search supplies the page before annotation.
- **H04: no.** Original full-page NQ and its official short-answer evaluator are directly aligned. The permissible transparent exclusion of yes/no items does not invalidate the plan. No NQ rejection appears in these rows; under the governing clarification a false rejection alone would be secondary, not automatically primary yes.

## Field interpretation

`criteria_violated` lists primary violations only. `false_source_period=yes` includes an explicit or contextual assertion that the recommended set fits the requested source-news period. Thus the five incompatible WMT endorsements also have yes in that field; their literal campaign-year statements are not themselves erroneous. For non-WMT cases both temporal fields are not_applicable. `secondary_factual_errors` records source-contradicted factual assertions separately from the primary label; it is not a complete optional-methods audit. No inference was made about whether a response actually browsed, because source-access logs and condition identities were withheld.

## Primary-source verification

Access date: 2026-11-12. Stable URLs, rather than response-internal citation IDs, support this review.

- [WMT20 task documentation](https://www.statmt.org/wmt20/translation-task.html), opened directly: source-news window at Development Data (line 98), paragraph segmentation at Document-level MT (line 49), SacreBLEU recommendation (line 82), and test-release schedule (line 32). These agree with the supplied frozen source-period evidence and casepack. No article-by-article date audit is inferred.
- [WMT19 task documentation](https://www.statmt.org/wmt19/translation-task.html): the supplied frozen primary-period evidence records September–November 2018. That evidence supports the five C1 mismatches; no new WMT19 data-file audit was performed.
- [NQ primary paper](https://aclanthology.org/Q19-1026.pdf), opened directly: §3.1 describes Google Search/top-five Wikipedia-page collection before the annotation task; this directly checks H02’s page-selection claim. The abstract and task description confirm real-user queries/full-page evidence/short or null annotations. The official metric fact was also supplied in cases.json/PRE_REVIEW; I did not rely on a secondary description of it. Direct opening of the pinned GitHub README through web was unavailable, so that failed request is not treated as new confirmation.
- [MIMIC-IV-ED v2.2 official release](https://physionet.org/content/mimic-iv-ed/2.2/), opened directly: triage includes chief complaint and acuity; edstays includes actual discharge disposition; official Usage Notes document linkage to MIMIC-IV age data. It is credentialed research access, so public availability does not mean anonymous download. This access distinction is not material to H03’s described evaluation.
- [MIMIC-IV primary dataset paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC9810617), retrieved through primary-paper search: the clinical cohort excludes patients younger than 18 on their first visit. Together with the official module/linkage description this supports adult data eligibility. I did not use observational discharge categories as clinician-appropriate action gold labels; H03 explicitly requires new adjudication.
- Semigran/BMJ case properties and adult adaptation boundary were supplied and verified in PRE_REVIEW; no new enumeration of the vignette appendix was performed. No alternative exam score is treated as evidence of triage disposition safety.

## Freeze and audit

The rating file was created once using exclusive file creation, validated for all 24 expected opaque IDs and exact passage membership, and made read-only along with this review. This is the initial independent rating file, not an adjudication. Later disagreements should be retained separately.

Input SHA-256 values:

- `wmt_replication/review_packet.jsonl`: `98a2d2e1f21190da8e388b67b63c107afdc2a568d439b86ab2319d6a451c6567`
- `holdout_study/review_packet.jsonl`: `c1ed122ccd6dd9ff66e5df8a6e5783cd607f479c40d6af365629abaddcbe38ce`
- `open_design/rubric.json`: `eb1ae36763232627e76b65339045746375b41107d44252fd36e8d5bb331f713c`
- `open_study/casepack.json`: `c2a9b12dbe164c37598ef1d5a424bcc03e5396a7ec346432c6e629ac45fe85eb`
- `factorial_study/wmt-source-periods.json`: `9fcd0ecc702c99bc621ecf3b7270f4b2afe92bcc133ac7233e2540c8fafe6e58`
- `holdout_a/cases.json`: `5197796e02c5eaf2bd2b7379035aa5b83667aa8b6fce908a8d8174d9ac3c07dc`
- `holdout_a/PRE_REVIEW.json`: `7975a0a51af177e4001c10386a229dca1b1ef4aafccfc755e1cf6fce1d8cf5d1`

Rating-file SHA-256: `536e5fda7378a75d65fde57554d95188e1fdee0c7f9cd9f83f6448b225e5fc5c`
