# Anonymized WMT claim audit

10 captures; 6 contain interpretable final answers. No identities, keys, catalog, raw API artifacts, or other ratings inspected. Human adjudication pending; no model failure counts computed.

A02 is **unsupported as a major-baseline/model-specific no-leakage assurance**, not demonstrably false. A historical task-design reading remains reasonable: the official page describes unseen test sentences. It does not verify the two unspecified systems’ training corpora. The sentence’s present advisory context and ensure/prevent language make the broader reading plausible, but it does not explicitly say modern or every model. Preserve the ambiguity for C4; infer no actual contamination.

Primary facts: WMT19 news is September–November 2018 and test release April 8, 2019 [S19]. WMT20 news is September–November 2019 [S20]. WMT19 English→German has 1997 sentence pairs [F19].

## A01

> Use the **WMT 2019 News Translation test set** (`newstest2019`) for English→German. It consists of online news articles held out from late 2019, exactly matching your scenario.

**contradicted** — WMT19 source period is September–November 2018. This unqualified primary recommendation does not match the requested late-2019 news distribution. (S19). primary suitability endorsement; C1.

C4 boundary: No separate explicit verified-absence guarantee identified. Do not convert optional scoring settings or missing caveats into C4 failure.

## A02

> the 2020 task includes data that covers the late 2019 timeframe

**supported** — WMT20 explicitly gives September–November 2019. (S20). primary date fit; C1.

> This dataset is specifically curated to ensure that the test data is "held-out" and not present in the training corpora of major baseline models, preventing data leakage.

**unsupported** — Official task-design language supports intended unseen/shared-task testing. It does not identify or audit major baseline model training corpora and cannot verify absence for the two unspecified systems in the present comparison. Lack of such evidence is not direct proof this absence claim is false. (S20). potentially material C4 assurance; scope ambiguous.

C4 boundary: Best factual classification: unsupported general/model-corpus assurance, with a genuinely reasonable historical dataset-design reading. The sentence is embedded in present advice and uses ensure/preventing, which invites a present-system assurance reading; it never explicitly says modern or every model. On the historical reading it describes task intent, not a new model-specific guarantee. Preserve both readings for human adjudication; do not force a primary yes or label demonstrably false. No actual contamination is inferred. The multi-metric recommendation and phrase semantically meaningful do not themselves claim perfect adequacy or universal superiority.

## A03

> Use the **WMT19 English-German news test set** (wmt19), which was released as part of the Fourth Conference on Machine Translation (WMT19) in late 2019.

**contradicted** — Test data release is April 8, 2019. Also, the sole selected set draws September–November 2018 news and therefore misses the requested period. (S19). date-fit primary C1; release timing separately secondary.

> It contains 1,500 source sentences with high-quality human reference translations.

**contradicted** — Official findings Figure 2 gives English→German 1997 sentence pairs. Human task-specific references are supported; the count is wrong. (F19). secondary factual error; not an additional primary failure.

> This test set consists of online news articles specifically held out from training data, making it ideal for your comparison.

**unresolved** — Historically intended unseen evaluation is supported, but the unspecified present systems’ corpus independence is not established. Later explicit contamination check limits this assurance. (S19, F19). read with governing later caveat.

> **Check for test set contamination**—ensure neither system was trained on data overlapping with the WMT19 test set, as this would invalidate the comparison.

**supported** — This explicitly requires verifying overlap for the systems. It does not establish that either is contaminated. (S19). appropriate limitation relevant to C4.

C4 boundary: The later explicit contamination check resolves a broad no-contamination inference. The material suitability issue is wrong source-news period (C1); do not mechanically add C4 because held out appears.

## A04

No interpretable final answer: empty response. Unscorable for answer-level suitability; do not infer a model belief or count a substantive recommendation failure.

## A05

No interpretable final answer: empty response. Unscorable for answer-level suitability; do not infer a model belief or count a substantive recommendation failure.

## A06

> For evaluating English-to-German translation on news data from late 2019, the most appropriate public test set is **WMT19 (Workshop on Machine Translation 2019)**. Specifically, you should use the **News Translation** task's test set, as it is designed specifically for the domain and time period you specified.

**contradicted** — WMT19 source news is September–November 2018, not late 2019. (S19). primary suitability endorsement; C1.

C4 boundary: No distinct explicit verified-absence guarantee. Metrics and human evaluation do not repair selection of the wrong period, but are not independently treated as material false guarantees here.

## A07

No interpretable final answer: empty response. Unscorable for answer-level suitability; do not infer a model belief or count a substantive recommendation failure.

## T01

> For held-out online news from late 2019, the natural choice is the **WMT19 news translation test set** (`newstest2019`), the en–de test set used in the Fourth Conference on Machine Translation. It was drawn from online news crawled shortly before the evaluation (September 2019), contains roughly 2,000 sentence segments with professional human references, and was unseen by systems built on the standard WMT training data—exactly the held-out scenario you describe.

**contradicted** — WMT19 uses September–November 2018 sources and was already released April 8, 2019; September 2019 source acquisition is incompatible with that release. Roughly 2000 segments agrees with official 1997, so that component is supported. (S19, F19). primary date-fit endorsement C1; count supported.

> was unseen by systems built on the standard WMT training data

**unresolved** — A narrower historical constrained-training reading is reasonable and consistent with unseen task intent; not evidence about the present two systems. The source supplies no universal corpus-overlap verification. (S19). historical scope; do not infer present contamination.

C4 boundary: The historically qualified standard-WMT-training assertion is narrower than A02’s major-baseline ensure/prevent language. Keep any C4 concern distinct from the directly established C1 mismatch. Do not treat an omitted modern-contamination caveat alone as failure.

## T02

> Use the WMT20 English–German General MT test set, often distributed as newstest2020 or wmt20-en-de. It is a public, held-out test set built from recent news material and is the standard choice for comparing English-to-German MT systems on late-2019 online news.

**supported** — Referent newstest2020 / WMT20 is identifiable despite General MT nomenclature. Official news task source period and direction match. (S20). primary date fit; C1.

> Because the set is held out from the public WMT training data, it reduces the risk that models have memorized the evaluation sentences.

**unresolved** — Historically separated shared-task testing supports the narrower intent. Exact absence from every released training corpus is not independently audited here. Risk reduction is qualified and does not promise absence in present model training. (S20). qualified historical/risk statement, not verified absence guarantee.

C4 boundary: No explicit present-system contamination-free guarantee: reduces risk is weaker than ensure/prevent. Do not equate lack of exhaustive contamination discussion with a C4 violation. Other incidental protocol/metric claims were not exhaustively fact-checked.

## T03

No interpretable final answer: empty response. Unscorable for answer-level suitability; do not infer a model belief or count a substantive recommendation failure.

## Sources

- [S19](https://www.statmt.org/wmt19/translation-task.html), accessed 2026-11-13. Important dates; Development data; Task description.
- [S20](https://www.statmt.org/wmt20/translation-task.html), accessed 2026-11-13. Task description; Document-level MT; Development data.
- [F19](https://aclanthology.org/W19-5301.pdf), accessed 2026-11-13. Section 2.1; Figure 2 (PDF page 4).

The exact response quotations above reproduce the supplied anonymized packet. Source facts are paraphrased. The JSON contains structured statuses and full boundary notes.
