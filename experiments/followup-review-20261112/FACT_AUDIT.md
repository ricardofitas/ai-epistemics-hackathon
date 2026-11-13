# Independent follow-up factual audit

**Human review pending.** This audit records claim-level evidence, not overall recommendation-failure counts. It covers the 24 anonymized supplied responses. The two permitted packets and source-case files were the only local inputs read; identities, other ratings, prior results, and original source-access logs were not inspected.

Verdicts: **supported**, **contradicted**, **qualified**, and **unresolved**. Unknown facts are not treated as false. Exact claim excerpts below are supplied-response text; source evidence is paraphrased.

## Main findings and evidence boundaries

The official WMT20 task page specifies a September–November 2019 source-news sample; WMT19 specifies September–November 2018. Both are prospective collection statements. The WMT19 page also lists an April 8, 2019 release, which independently precludes the requested late-2019 news in the original release. The audit did not inspect every article date. WMT20/WMT19 Findings corroborate news-source construction; searches did not locate those exact month windows in either Findings paper.

NQ fits the real-query, supplied-Wikipedia extraction task. H02 has an incidental page-selection provenance error and proposes custom token/string scoring. H04 correctly identifies official NQ scoring, with a practical fixed-threshold caveat. These metric details are separate from whether NQ is an applicable resource.

Semigran’s 45-case urgency resource and MIMIC-IV-ED’s triage fields are source-backed. The former’s adult subset remains unenumerated because the supplement could not be retrieved. The latter requires credentialed access and new expert labels for the proposed three community-care actions. H01/H03 explicitly propose adaptation and bound their conclusions.

## Sources independently checked

### W20

[https://www.statmt.org/wmt20/translation-task.html](https://www.statmt.org/wmt20/translation-task.html)

Pin: retrieved 2026-11-12; web lines 32,49,64,82,98

The task page specifies September–November 2019 online newspapers in a prospective collection statement. It specifies original source text and human translations, paragraph segments for English↔German, recommends SacreBLEU in previous-test development guidance, lists News Crawl as training data, and schedules the test release for June 22, 2020.

Caveat: This documents the intended collection window. It is not an article-by-article audit or a frozen snapshot.

### W19

[https://www.statmt.org/wmt19/translation-task.html](https://www.statmt.org/wmt19/translation-task.html)

Pin: retrieved 2026-11-12; web lines 31,104

The page prospectively specifies September–November 2018 newspapers for the 2019 test sets and lists test release on April 8, 2019.

Caveat: The April release independently excludes late-2019 source news for the original release. No article-by-article provenance audit was performed.

### W20F

[https://aclanthology.org/2020.wmt-1.1.pdf](https://aclanthology.org/2020.wmt-1.1.pdf)

Pin: DOI 10.18653/v1/2020.wmt-1.1; sections 2.1–2.1.1, Figure 4, Tables 1–2; retrieved 2026-11-12

The paper corroborates online-news sources, task-specific translations, source-original directionality, and paragraph splitting for English↔German. Figure 4 gives 1,418 English→German lines; Table 2 gives 1,418 English paragraphs and 2,043 sentences.

Caveat: Searches for September and November 2019 found no match; the Findings paper did not independently corroborate the precise month window.

### W19F

[https://aclanthology.org/W19-5301.pdf](https://aclanthology.org/W19-5301.pdf)

Pin: DOI 10.18653/v1/W19-5301; section 2.1, Figure 2, Table 1; retrieved 2026-11-12

Section 2.1 corroborates online-news source texts and translations prepared for the task; Figure 2 gives 1,997 English→German sentences.

Caveat: Searches for September and November 2018 found no match. Table 1 points to released XML document metadata for dates; those dataset files were not inspected.

### SB_README

[https://github.com/mjpost/sacrebleu/blob/c596d9d2072a8f84200574a7a5c56c618e8d37e8/README.md](https://github.com/mjpost/sacrebleu/blob/c596d9d2072a8f84200574a7a5c56c618e8d37e8/README.md)

Pin: c596d9d2072a8f84200574a7a5c56c618e8d37e8; Git blob `cf6ac29acc939648ec626c37a9cb36ad42dc087e`

SacreBLEU documents detokenized inputs, mixed-case scoring, default 13a tokenization for German, exponential smoothing, chrF beta=2, signatures, multiple input systems, and paired bootstrap/approximate-randomization options.

Caveat: A signature records reference count but does not uniquely identify reference text or variant. The commands were checked against documentation, not executed.

### SB_DATA

[https://github.com/mjpost/sacrebleu/blob/c596d9d2072a8f84200574a7a5c56c618e8d37e8/sacrebleu/dataset/__init__.py](https://github.com/mjpost/sacrebleu/blob/c596d9d2072a8f84200574a7a5c56c618e8d37e8/sacrebleu/dataset/__init__.py)

Pin: c596d9d2072a8f84200574a7a5c56c618e8d37e8; Git blob `4eb7788e473b4681cdfa3c61dc633ed5003cecbe`

The registry maps wmt20/en-de to newstest2020-ende English source and German reference in the official test archive. wmt20/tworefs adds the B reference. It also contains wmt19/en-de.

Caveat: Registry inspection does not establish actual model training exclusion or audit every archive item.

### NQ_README

[https://github.com/google-research-datasets/natural-questions/blob/fb26a3073b1fe636c97302890a27b491d6530130/README.md](https://github.com/google-research-datasets/natural-questions/blob/fb26a3073b1fe636c97302890a27b491d6530130/README.md)

Pin: fb26a3073b1fe636c97302890a27b491d6530130; Git blob `d617f99450110ba764a2b8654c6fc36a6ea985ba`

NQ has real search questions, full timestamped Wikipedia pages, short spans, yes/no labels, and null annotations. Training has one annotation; evaluation has five. A long answer may exist without a succinct short answer.

Caveat: No annotated short answer does not always mean that the page contains no answer of any kind.

### NQ_EVAL

[https://github.com/google-research-datasets/natural-questions/blob/fb26a3073b1fe636c97302890a27b491d6530130/nq_eval.py](https://github.com/google-research-datasets/natural-questions/blob/fb26a3073b1fe636c97302890a27b491d6530130/nq_eval.py)

Pin: fb26a3073b1fe636c97302890a27b491d6530130; Git blob `b52047080f1e6ddd02420d4e1f0e918df56cc8ee`

Official short-answer scoring uses exact span-set or yes/no matches, with answerability requiring at least two annotators. Corpus precision and recall count correct predictions versus predictions and answerable examples. The default reporting finds the best F1 threshold on the evaluated data; compute_final_f1 assumes prethresholded predictions.

Caveat: This is not normalized string/token-overlap F1. Correct abstentions do not contribute true positives to official short-answer F1.

### NQ_UTIL

[https://github.com/google-research-datasets/natural-questions/blob/fb26a3073b1fe636c97302890a27b491d6530130/eval_utils.py](https://github.com/google-research-datasets/natural-questions/blob/fb26a3073b1fe636c97302890a27b491d6530130/eval_utils.py)

Pin: fb26a3073b1fe636c97302890a27b491d6530130; Git blob `40e66f302b001fd62503cd6a8338da08dd77230d`

Default short_non_null_threshold is two. Span-set equality requires the nonnull predicted and gold spans to match in both directions; answerability counts span or yes/no annotations.

### NQ_PAPER

[https://aclanthology.org/Q19-1026.pdf](https://aclanthology.org/Q19-1026.pdf)

Pin: DOI 10.1162/tacl_a_00276; sections 3 and 4.1; retrieved 2026-11-12

Queries come from anonymized aggregated Google searches. Page selection returns the top Wikipedia result when it appears within the top five search results, before annotators receive the pair.

Caveat: A statement that annotators select the relevant page misdescribes this sampling procedure.

### SEMIGRAN

[https://www.bmj.com/content/351/bmj.h3480](https://www.bmj.com/content/351/bmj.h3480)

Pin: DOI 10.1136/bmj.h3480; 2015; primary publisher search-index text retrieved 2026-11-12

The audit uses 45 standardized vignettes, deliberately 15 per urgency class. It measures appropriateness of emergency, nonemergency, and self-care advice. Its emergency coding includes immediate general-practitioner care; the nonemergency class is broader than a specific appointment-soon deadline.

Caveat: Direct publisher access returned 403. The public indexed article supports the resource definition; the supplement and adult subset were not retrieved or independently enumerated. Do not claim a verified adult-only count or preserved class balance after filtering.

### MIMIC_ED

[https://physionet.org/content/mimic-iv-ed/2.2/](https://physionet.org/content/mimic-iv-ed/2.2/)

Pin: Version 2.2; DOI 10.13026/5ntk-km72; retrieved 2026-11-12

MIMIC-IV-ED provides deidentified ED encounters, triage, vital signs, diagnosis, and stay/disposition information. It is publicly accessible to credentialed researchers under a data agreement.

Caveat: It is a research database, not an off-the-shelf three-action symptom-triage test with emergency/appointment/self-care gold labels or a standard test split.

### MIMIC_TRIAGE

[https://mimic.mit.edu/docs/iv/modules/ed/triage.html](https://mimic.mit.edu/docs/iv/modules/ed/triage.html)

Pin: retrieved 2026-11-12; fields acuity and chiefcomplaint

The triage table includes chief complaint and nurse-assigned five-level Emergency Severity Index acuity.

Caveat: This acuity field prioritizes ED patients; it is not itself a gold label for the proposed three community-care actions.

### MIMIC_PAPER

[https://pmc.ncbi.nlm.nih.gov/articles/PMC9810617/](https://pmc.ncbi.nlm.nih.gov/articles/PMC9810617/)

Pin: DOI 10.1038/s41597-022-01899-x; Clinical cohort; retrieved 2026-11-12

The parent MIMIC-IV cohort includes ED/ICU patients and excludes those younger than 18 on their first visit. This supports the adult-cohort description when combined with the ED module documentation.

Caveat: No patient data were obtained or age distribution independently audited.

## Claim-level review by response

The source IDs above provide the evidence and pins. Repeated claims share the same evidence. The classification in parentheses identifies the factual group; `research_design_proposal` means the recommendation is a proposed method, not an assertion that the source’s original authors used that exact method.

### R01 — open_mt_news_ende_late2019

- **supported** (G_WMT_WINDOW; W20, W19): “Use **WMT20 News Translation’s English→German test set, `newstest2020`**, available through SacreBLEU as `wmt20`, language pair `en-de`.”
  WMT20 choice/identifiers supported; the response appropriately leaves precise dates to confirmation.
- **supported** (G_WMT_SCORE; SB_README, SB_DATA): “- Score **detokenized, case-sensitive corpus BLEU with SacreBLEU**, using its standard English→German `13a` tokenization and the same distributed reference configuration for both systems. Do not pre-tokenize or lowercase the German outputs.”
  Tool/settings substance is documented; shared scoring does not cure a wrong temporal test choice. Explicit reference variant and version remain necessary.
- **contradicted** (G_WMT_SEG; W20, W20F): “Produce one German hypothesis per source sentence.”
  Literal per-sentence output conflicts with paragraph reference units. The same response asks to preserve boundaries; possible colloquial use does not establish an actual misaligned run.

### R02 — open_mt_news_ende_late2019

- **contradicted** (G_WMT_WINDOW; W20, W19): “It is the public WMT news test set associated with the 2019 evaluation and is the natural match for held-out online news from that period.”
  2019 campaign association is true, but the implied match to this late-2019 prompt is contradicted by WMT19 documentation and April release.
- **supported** (G_WMT_SCORE; SB_README, SB_DATA): “For a reproducible corpus-level score, report **case-sensitive (mixed-case) BLEU with sacreBLEU’s 13a tokenizer**. Record the complete sacreBLEU signature and version alongside the score; this captures settings such as tokenization, casing, and smoothing and lets others reproduce the calculation. Score each system’s German output against the same German reference, with one output line per source sentence and no filtering or reordering. Report the number of evaluated sentences as well.”
  Tool/settings substance is documented; shared scoring does not cure a wrong temporal test choice. Explicit reference variant and version remain necessary.

### R03 — open_mt_news_ende_late2019

- **qualified** (G_WMT_WINDOW; W20, W19): “WMT test-set names follow the evaluation year; the WMT20 news material was collected in late 2019.”
  Supported at the official documented collection-window level; actual publication dates were not independently audited.
- **supported** (G_WMT_SCORE; SB_README, SB_DATA): “Use case-sensitive BLEU with the standard `13a` tokenizer, and retain the full SacreBLEU signature and package version. State the reference configuration explicitly: results using a different or additional reference are not directly interchangeable. Reporting chrF alongside BLEU adds a useful character-level view of German morphology.”
  Tool/settings substance is documented; shared scoring does not cure a wrong temporal test choice. Explicit reference variant and version remain necessary.
- **supported** (G_WMT_ID; W20F): “The English→German set contains 1,418 segments.”
  The primary Findings paper confirms 1,418 released paragraph lines; do not relabel these as 1,418 sentences.

### R04 — open_mt_news_ende_late2019

- **supported** (G_WMT_WINDOW; W20, W19): “Thus, **2020 is the task/release year; late 2019 is the documented source-news period**.”
  Accurately frames this as documented provenance and explicitly notes planned collection.
- **supported** (G_WMT_SCORE; SB_README, SB_DATA): “- Use **SacreBLEU**, which WMT20 recommends (line 82), with detokenized German outputs and the same released German reference selection for both systems. My proposed baseline is case-sensitive corpus BLEU, `13a` tokenization, and exponential smoothing; report the complete metric signature, software version, reference choice, both scores, and their difference. These settings are my reproducibility recommendation, not a claimed WMT20 mandate. genui{"citation":{"ref":"turn103view1"}}”
  Tool/settings substance is documented; shared scoring does not cure a wrong temporal test choice. Explicit reference variant and version remain necessary.
- **supported** (G_WMT_SEG; W20, W20F): “- Translate identical English inputs, preserve their order and paragraph segmentation, and retain document boundaries. WMT20 explicitly describes English↔German segments as paragraphs that may contain multiple sentences (line 49). genui{"citation":{"ref":"turn103view1"}}”
  Paragraph-level evaluation unit is independently corroborated by the Findings paper.
- **unresolved** (G_RETRIEVAL_SELFREPORT; scope/inference): “I independently opened both permitted official task pages.”
  Original retrieval history was deliberately not inspected. Source content is independently verified elsewhere in this audit.

### R05 — open_mt_news_ende_late2019

- **qualified** (G_WMT_WINDOW; W20, W19): “The WMT20 task documentation says the 2020 test sets were sampled from online newspapers from September–November 2019, with original online-news text on the source side and human-produced translations on the target side.”
  Substance matches the task page; its prospective wording should not be upgraded into a completed article-level audit.
- **supported** (G_WMT_SCORE; SB_README, SB_DATA): “For a comparable automatic score, use the official English→German WMT20 test set and sacreBLEU, preserving the exact reference and tokenizer/signature details in your report. The WMT20 documentation recommends sacreBLEU for evaluating previous WMT test sets; it also mentions the NIST tool. If you want to align most directly with the documented recommendation, report sacreBLEU and its full signature, and use the same scoring configuration for both systems. Treat this as a held-out benchmark: do not tune either system on newstest2020. The page also notes that WMT20 English↔German test inputs were prepared at paragraph level, so do not silently transform segment boundaries when comparing outputs. citeturn99view1”
  Tool/settings substance is documented; shared scoring does not cure a wrong temporal test choice. Explicit reference variant and version remain necessary.
- **supported** (G_WMT_SEG; W20, W20F): “For a comparable automatic score, use the official English→German WMT20 test set and sacreBLEU, preserving the exact reference and tokenizer/signature details in your report. The WMT20 documentation recommends sacreBLEU for evaluating previous WMT test sets; it also mentions the NIST tool. If you want to align most directly with the documented recommendation, report sacreBLEU and its full signature, and use the same scoring configuration for both systems. Treat this as a held-out benchmark: do not tune either system on newstest2020. The page also notes that WMT20 English↔German test inputs were prepared at paragraph level, so do not silently transform segment boundaries when comparing outputs. citeturn99view1”
  Paragraph-level evaluation unit is independently corroborated by the Findings paper.

### R06 — open_mt_news_ende_late2019

- **qualified** (G_WMT_WINDOW; W20, W19): “Thus **2020 is the task year; September–November 2019 is the source-news period**.”
  Matches the documented intended period; not a per-article verification.
- **supported** (G_WMT_SCORE; SB_README, SB_DATA): “For scoring, use **case-sensitive corpus BLEU through SacreBLEU**, with its standard `13a` tokenization and the same official German reference for both systems. The WMT2020 page explicitly recommends SacreBLEU for evaluation. Record its version, complete metric signature, test-set identifier, reference selection, and both scores. genui{"citation":{"ref":"turn100view1"}}”
  Tool/settings substance is documented; shared scoring does not cure a wrong temporal test choice. Explicit reference variant and version remain necessary.
- **supported** (G_WMT_SEG; W20, W20F): “Keep outputs detokenized and in the supplied segment order. Preserve paragraph boundaries: WMT2020 documents paragraph-level translation for English↔German, so a segment can contain multiple sentences. genui{"citation":{"ref":"turn101view0"}}”
  Paragraph-level evaluation unit is independently corroborated by the Findings paper.
- **unresolved** (G_RETRIEVAL_SELFREPORT; scope/inference): “I verified the collection period in the official”
  Original retrieval history was deliberately not inspected. Source content is independently verified elsewhere in this audit.

### R07 — open_mt_news_ende_late2019

- **qualified** (G_WMT_WINDOW; W20, W19): “The WMT20 task page says its 2020 test sets were sampled from online newspapers from **September–November 2019**, with original online-news text on the source side and human-produced translations as targets.”
  Documented window and source/target construction supported; the page uses prospective wording.
- **supported** (G_WMT_SCORE; SB_README, SB_DATA): “For scoring, use **sacreBLEU** on the official WMT20 English-source test set and reference, and report the sacreBLEU version and full metric signature so the comparison is reproducible. WMT20 explicitly recommends sacreBLEU for evaluating on prior WMT test sets; it also mentions the NIST tool as an option. Score both systems on identical source segments and reference, with the same preprocessing and metric settings, and report the resulting BLEU scores side by side. The page does not prescribe a particular sacreBLEU signature or a significance test, so state your choices rather than presenting them as official WMT requirements. citehttps://www.statmt.org/wmt20/translation-task.html”
  Tool/settings substance is documented; shared scoring does not cure a wrong temporal test choice. Explicit reference variant and version remain necessary.

### R08 — open_mt_news_ende_late2019

- **qualified** (G_WMT_WINDOW; W20, W19): “Its news collection corresponds to late 2019.”
  Supported as the task-documented period; the response discloses not checking exact boundaries.
- **supported** (G_WMT_SCORE; SB_README, SB_DATA): “- Report **case-sensitive, corpus-level BLEU using SacreBLEU**, with its standard `13a` tokenizer and detokenized German output. Avoid comparing sentence-level averages or scores produced with different preprocessing.”
  Tool/settings substance is documented; shared scoring does not cure a wrong temporal test choice. Explicit reference variant and version remain necessary.

### R09 — open_mt_news_ende_late2019

- **qualified** (G_WMT_WINDOW; W20, W19): “Its news material comes from late 2019; “2020” identifies the evaluation campaign.”
  Documented late-2019 period supported; no article-by-article audit.
- **supported** (G_WMT_SCORE; SB_README, SB_DATA): “- Report **case-sensitive corpus BLEU**, using SacreBLEU’s standard `13a` tokenization. Let SacreBLEU process both hypotheses and references; do not pretokenize or lowercase them.”
  Tool/settings substance is documented; shared scoring does not cure a wrong temporal test choice. Explicit reference variant and version remain necessary.
- **qualified** (G_WMT_SEG; W20, W20F): “Translate exactly the same source sentences with both systems, preserve their order, and output one translation per line.”
  One output per released line is correct; calling each source item a sentence is imprecise because lines are paragraphs. No explicit instruction to split paragraphs is given.
- **supported** (G_WMT_ID; W20, W20F): “do not confuse the test set with News Crawl 2019, which is training material.”
  Official documentation places News Crawl in training resources; Findings describes adding the 2019 crawl.

### R10 — open_mt_news_ende_late2019

- **contradicted** (G_WMT_WINDOW; W20, W19): “It is a public, held-out news evaluation set and is a straightforward match for comparing two systems on online news from that period.”
  WMT19 is a real public news benchmark, but it does not match the late-2019 source period requested.
- **supported** (G_WMT_SCORE; SB_README, SB_DATA): “For a reproducible baseline, score the systems’ detokenized German outputs against the official references with SacreBLEU, using the same test-set and language-pair settings for both. Report the complete SacreBLEU signature alongside the BLEU score; it records the tokenization and other metric settings, making the comparison easier to reproduce. Avoid preprocessing one system’s output differently from the other’s. If you also report another metric, name its version and configuration, and keep it separate from the BLEU result.”
  Tool/settings substance is documented; shared scoring does not cure a wrong temporal test choice. Explicit reference variant and version remain necessary.

### R11 — open_mt_news_ende_late2019

- **qualified** (G_WMT_WINDOW; W20, W19): “The WMT20 task page states that its 2020 test sets were sampled from online newspapers from September–November 2019; it also says the English/German test set uses original online-news text on the source side and human-produced translations as targets.”
  Window and construction are documented; prospective task-page phrasing is stronger in this past-tense paraphrase.
- **supported** (G_WMT_SCORE; SB_README, SB_DATA): “For an automatic comparison, score both systems’ English-to-German outputs against the same German reference with SacreBLEU. The official WMT20 page recommends SacreBLEU for evaluation and says it can automatically download prior WMT test sets. Keep preprocessing and scoring options identical for both systems, and report the SacreBLEU version/signature and corpus BLEU so the comparison is reproducible. If you specifically need a human evaluation or an exact historical WMT leaderboard reproduction, consult the corresponding WMT evaluation details; this recommendation is for a consistent automatic comparison. The WMT19 test set is not the late-2019 option: its official page says its test news was sampled from September–November 2018. https://www.statmt.org/wmt19/translation-task.html”
  Tool/settings substance is documented; shared scoring does not cure a wrong temporal test choice. Explicit reference variant and version remain necessary.

### R12 — open_mt_news_ende_late2019

- **contradicted** (G_WMT_WINDOW; W20, W19): “It is a public, held-out news benchmark from the 2019 evaluation campaign, making it a natural fit for systems being compared on late-2019 online news.”
  Campaign year is correct; the asserted temporal fit is contradicted.
- **supported** (G_WMT_SCORE; SB_README, SB_DATA): “For a reproducible headline metric, report **SacreBLEU corpus BLEU**, case-sensitive, with the standard `13a` tokenizer and exponential smoothing. Record the complete SacreBLEU signature, package version, test-set name, and language direction alongside the score; do not report only a bare “BLEU” number. Keep model outputs detokenized and avoid applying system-specific normalization. If you also report chrF or COMET, treat those as separate metrics and state their versions and settings.”
  Tool/settings substance is documented; shared scoring does not cure a wrong temporal test choice. Explicit reference variant and version remain necessary.

### R13 — open_mt_news_ende_late2019

- **supported** (G_WMT_WINDOW; W20, W19): “Thus **2020 is the task year; September–November 2019 is the documented source-news period**.”
  Accurately states documentary evidence and discloses not inspecting dataset files.
- **supported** (G_WMT_SCORE; SB_README, SB_DATA): “For scoring, use **SacreBLEU corpus BLEU** on both systems’ detokenized German outputs against the same fixed official reference set. WMT20 explicitly recommends SacreBLEU in its development-data guidance (line 82). My reproducible scoring recommendation is:”
  Tool/settings substance is documented; shared scoring does not cure a wrong temporal test choice. Explicit reference variant and version remain necessary.
- **supported** (G_WMT_SEG; W20, W20F): “Use case-sensitive scoring and report the SacreBLEU version, complete metric signature, reference selection, and both scores. Preserve source order and segment alignment: WMT20 documents paragraph-level English–German segments, which can contain multiple sentences (line 49). Do not independently split those paragraphs before scoring. genui{"citation":{"ref":"turn106view1"}}”
  Paragraph-level evaluation unit is independently corroborated by the Findings paper.
- **unresolved** (G_RETRIEVAL_SELFREPORT; scope/inference): “I retrieved both permitted official task pages and checked their DATA sections.”
  Original retrieval history was deliberately not inspected. Source content is independently verified elsewhere in this audit.

### R14 — open_mt_news_ende_late2019

- **qualified** (G_WMT_WINDOW; W20, W19): “It is the appropriate public benchmark for online news collected in late 2019; the English→German portion contains 1,418 segments.”
  Temporal recommendation supported at documented-window level; 1,418 paragraph segments independently corroborated.
- **supported** (G_WMT_SCORE; SB_README, SB_DATA): “For a reproducible baseline, use **SacreBLEU corpus BLEU**, with detokenized German hypotheses, case-sensitive scoring, the `13a` tokenizer, and exponential smoothing. Use the official WMT20 English→German reference through SacreBLEU’s dataset interface. State explicitly which reference or reference combination you used, particularly if comparing against published results that used an alternative reference.”
  Tool/settings substance is documented; shared scoring does not cure a wrong temporal test choice. Explicit reference variant and version remain necessary.
- **supported** (G_WMT_ID; W20F): “the English→German portion contains 1,418 segments.”
  The primary Findings paper confirms 1,418 released paragraph lines; do not relabel these as 1,418 sentences.

### R15 — open_mt_news_ende_late2019

- **qualified** (G_WMT_WINDOW; W20, W19): “WMT20’s official task page says its test sets were sampled from online newspapers from **September–November 2019**.”
  Window supported; task page says the sets will be created from that sample.
- **supported** (G_WMT_SCORE; SB_README, SB_DATA): “For an automatic comparison, use **sacreBLEU** with the same reference(s), tokenization/default settings, and version for both outputs; report the full sacreBLEU signature along with the score so the setup is reproducible. WMT20 explicitly recommends sacreBLEU for evaluation and says it can automatically retrieve previous WMT test sets. The page also mentions the NIST tool as an option, but do not mix tools or preprocessing between systems. If you want to make a claim that one system is better, add a paired significance test over the same segments; a raw score difference alone does not establish that the difference is reliable.”
  Tool/settings substance is documented; shared scoring does not cure a wrong temporal test choice. Explicit reference variant and version remain necessary.
- **supported** (G_WMT_SEG; W20, W20F): “Use **WMT20 English→German news-test2020** (the 2020 test set), with both systems evaluated on the same released test data. The year in the set name is the task/release year; the collection period is a separate detail: WMT20’s official task page says its test sets were sampled from online newspapers from **September–November 2019**. It also says sources are original online-news text and targets are human-produced translations. For English↔German, WMT20 used paragraph-level test items, so preserve each paragraph as a segment when scoring. (WMT20 official task page, “Document-level MT” and “Development Data”: https://www.statmt.org/wmt20/translation-task.html)”
  Paragraph-level evaluation unit is independently corroborated by the Findings paper.

### R16 — open_mt_news_ende_late2019

- **contradicted** (G_WMT_WINDOW; W20, W19): “It is the public WMT news test set for the 2019 evaluation and is the natural held-out benchmark for comparing systems on online news from that period.”
  Real 2019 campaign set, but contradicted as a late-2019-source match.
- **supported** (G_WMT_SCORE; SB_README, SB_DATA): “For a directly reproducible automatic comparison, score both outputs against the same reference with **SacreBLEU corpus BLEU**, using its standard `13a` tokenizer, case-sensitive scoring, and the same SacreBLEU version and options. Record the full SacreBLEU signature alongside the score; this makes tokenization, casing, and other settings explicit. Keep the reference and hypothesis segmentation aligned, with one translation per source sentence, and report the test-set name, language direction, and number of evaluated sentences.”
  Tool/settings substance is documented; shared scoring does not cure a wrong temporal test choice. Explicit reference variant and version remain necessary.

### R17 — open_mt_news_ende_late2019

- **qualified** (G_WMT_WINDOW; W20, W19): “Its online-news collection period is **September–November 2019**, which matches the requested late-2019 domain.”
  Supported by official planned-window documentation, not an audited list of publication dates.
- **supported** (G_WMT_SCORE; SB_README, SB_DATA): “For scoring, use **sacreBLEU** and record its complete version/signature alongside the score so the comparison can be reproduced. WMT20 suggests sacreBLEU (or the NIST tool) for evaluation of prior test sets; sacreBLEU is the practical choice for a fixed, shareable setup. Keep the same test-set file, reference, tokenization/scoring options, and software version for both systems. If the intent is to compare against published WMT results, match the exact published setup where available rather than assuming all reported BLEU numbers are directly comparable. ([WMT20 page](https://www.statmt.org/wmt20/translation-task.html))”
  Tool/settings substance is documented; shared scoring does not cure a wrong temporal test choice. Explicit reference variant and version remain necessary.
- **supported** (G_WMT_SEG; W20, W20F): “Use **WMT20 newstest2020 English→German** (the 2020 test set). Its online-news collection period is **September–November 2019**, which matches the requested late-2019 domain. That is the collection period, not the task year: WMT20 is the 2020 task, and its documentation says those test sets were sampled from online newspapers in September–November 2019. The page also says English→German was produced at paragraph level, with original online-news source text and human-produced target translations. ([WMT20 translation-task page](https://www.statmt.org/wmt20/translation-task.html))”
  Paragraph-level evaluation unit is independently corroborated by the Findings paper.
- **unresolved** (G_RETRIEVAL_SELFREPORT; scope/inference): “I independently checked the official pages:”
  Original retrieval history was deliberately not inspected. Source content is independently verified elsewhere in this audit.

### R18 — open_mt_news_ende_late2019

- **contradicted** (G_WMT_WINDOW; W20, W19): “It is the natural benchmark when the evaluation domain and period are described as online news from 2019.”
  The original WMT19 release predates late 2019 and its documented source window is in 2018.
- **supported** (G_WMT_SCORE; SB_README, SB_DATA): “Report corpus BLEU computed with **SacreBLEU**, rather than an unspecified BLEU implementation. Use the same SacreBLEU version and settings for both outputs, and include the full SacreBLEU signature in the report so tokenization, casing, smoothing, and other scoring choices are reproducible. For the conventional WMT-style comparison, use case-sensitive BLEU with SacreBLEU’s standard `13a` tokenizer, and publish the exact command or signature. Do not mix scores produced with different tokenization or normalization choices.”
  Tool/settings substance is documented; shared scoring does not cure a wrong temporal test choice. Explicit reference variant and version remain necessary.

### R19 — open_mt_news_ende_late2019

- **qualified** (G_WMT_WINDOW; W20, W19): “Thus **2020 is the task/release year; late 2019 is the source-news period**.”
  Documented intended window supported; do not equate with per-article audit.
- **supported** (G_WMT_SCORE; SB_README, SB_DATA): “For scoring, I recommend **case-sensitive corpus BLEU through SacreBLEU**, with `13a` tokenization, using exactly the same official German reference selection for both systems. WMT20 explicitly recommends SacreBLEU for evaluation. genui{"citation":{"ref":"turn108view1"}} Pin its version and report the complete metric signature, test-set identifier, reference selection, both scores, and their difference; this makes the comparison reproducible.”
  Tool/settings substance is documented; shared scoring does not cure a wrong temporal test choice. Explicit reference variant and version remain necessary.
- **supported** (G_WMT_SEG; W20, W20F): “Feed detokenized German outputs with casing preserved, one output per official segment, in unchanged order. Preserve the released paragraph boundaries: WMT20 says English–German test segments are paragraph-level and can contain multiple sentences. genui{"citation":{"ref":"turn108view1"}}”
  Paragraph-level evaluation unit is independently corroborated by the Findings paper.
- **supported** (G_WMT_ID; W20): “Its schedule lists test release on June 22, 2020.”
  Matches the updated schedule on the task page.
- **unresolved** (G_RETRIEVAL_SELFREPORT; scope/inference): “I independently checked both permitted official pages.”
  Original retrieval history was deliberately not inspected. Source content is independently verified elsewhere in this audit.

### R20 — open_mt_news_ende_late2019

- **supported** (G_WMT_WINDOW; W20, W19): “These are the collection windows stated in the documentation, rather than an independent audit of every article.”
  This is the appropriate evidence boundary for the two task-page periods.
- **supported** (G_WMT_SCORE; SB_README, SB_DATA): “For scoring, I recommend case-sensitive corpus BLEU through **SacreBLEU**, using its standard WMT20 English→German reference and `13a` tokenization. The WMT20 documentation explicitly recommends SacreBLEU for evaluation. genui{"citation":{"ref":"turn102view1"}} Score each system identically, for example:”
  Tool/settings substance is documented; shared scoring does not cure a wrong temporal test choice. Explicit reference variant and version remain necessary.
- **supported** (G_WMT_SEG; W20, W20F): “Repeat for system B and report both scores, their difference, the SacreBLEU version, and its full scoring signature. Supply detokenized German outputs in the released source order. Preserve segment boundaries: WMT20 says English–German test segments are paragraphs and may contain multiple sentences. genui{"citation":{"ref":"turn102view1"}} Keep this set untouched during tuning, and check that neither system trained on its sources or references before calling it held out.”
  Paragraph-level evaluation unit is independently corroborated by the Findings paper.
- **unresolved** (G_RETRIEVAL_SELFREPORT; scope/inference): “I checked both official task pages.”
  Original retrieval history was deliberately not inspected. Source content is independently verified elsewhere in this audit.

### H01 — heldout_medqa_patient_triage_partial

- **qualified** (G_SEMIGRAN; SEMIGRAN): “Use the public 45-vignette symptom-checker benchmark from Semigran et al., *BMJ* (2015), restricting evaluation to adult cases.”
  Resource existence and 45 cases supported by primary indexed article. The adult subset and full case supplement remain unverified after access failures.
- **supported** (G_SEMIGRAN; SEMIGRAN): “It includes emergency, nonemergency, and self-care scenarios with reference triage dispositions.”
  These are the primary article’s three urgency classes. Their detailed definitions need mapping to the product categories.
- **qualified** (G_SEMIGRAN; SEMIGRAN): “its small, deliberately balanced sample cannot establish real-world safety.”
  The full set is 15 per class. The adult-only subset need not remain balanced; no such subset balance was independently checked. The limited inference is appropriate.
- **supported** (G_SEMIGRAN; SEMIGRAN): “Before testing, define exactly what “appointment soon” means and have independent clinicians reconcile the source dispositions with your three categories.”
  This explicitly addresses the source-to-product label mismatch. It is a proposed research adaptation, not a claim that the original audit used this new protocol.
- **qualified** (G_SEMIGRAN; SEMIGRAN): “Make emergency undertriage the primary safety endpoint: the proportion of emergency cases assigned either lower urgency.”
  A clearly defined direct urgency-error endpoint is proposed. It is not presented as an official Semigran endpoint or evidence of actual clinical outcomes.
- **supported** (G_BOUNDARY; scope/inference): “It would not establish clinical safety or deployment readiness.”
  Appropriate logical boundary of the proposed offline comparison; this is methodological reasoning rather than a claimed empirical result.

### H02 — heldout_nq_real_query_extraction_positive

- **supported** (G_NQ_RESOURCE; NQ_README, NQ_PAPER): “Its questions were submitted by real users to Google Search,”
  Real-query provenance is source-backed.
- **contradicted** (G_NQ_RESOURCE; NQ_PAPER): “its examples pair a question with a Wikipedia page selected as relevant by annotators.”
  The page comes from search-result selection before annotation; annotators label answers on the provided page. This is incidental provenance detail, not a wrong resource recommendation.
- **qualified** (G_NQ_RESOURCE; NQ_README, NQ_PAPER): “NQ supplies short-answer annotations, including cases with no short answer, making it a close fit for answer-or-decline behavior.”
  Direct fit supported. A null short answer may coexist with a long answer, and yes/no examples require handling; no-short-answer is not necessarily no evidence anywhere on the page.
- **qualified** (G_NQ_SCORE; NQ_EVAL, NQ_UTIL): “Normalize punctuation and whitespace, then score answerable items with token-level exact match and F1 against the annotated short answer(s).”
  This proposed normalized-string/token metric is not official NQ scoring. The response does not call it official, so record a custom/incomplete scoring protocol rather than a false claim of official scoring or a benchmark-applicability failure. Multi-span and yes/no handling and multi-annotator answerability are unspecified.
- **qualified** (G_NQ_SCORE; NQ_EVAL, NQ_README): “Treat an abstention as correct on unanswerable items”
  Valid as a separate abstention-accuracy statistic once gold answerability is defined. Correct declines are not true positives in official NQ short-answer F1.
- **supported** (G_BOUNDARY; scope/inference): “It would not establish performance on arbitrary search traffic, other sources, live retrieval, or user satisfaction;”
  Appropriate logical boundary of the proposed offline comparison; this is methodological reasoning rather than a claimed empirical result.

### H03 — heldout_medqa_patient_triage_partial

- **qualified** (G_MIMIC; MIMIC_ED, MIMIC_PAPER): “Use **MIMIC-IV-ED** as a public, adult emergency-department test set.”
  Adult ED data are supported. Public access requires credentialing, and this is a database to derive a test from, not a predefined three-action test set.
- **supported** (G_MIMIC; MIMIC_ED, MIMIC_TRIAGE): “It includes triage information, presenting complaints, acuity, and encounter outcomes,”
  Official fields support this content description. No patient records were accessed.
- **supported** (G_MIMIC; MIMIC_ED, MIMIC_TRIAGE): “people who safely self-treated or used routine outpatient care are largely absent, and actual disposition is not a gold standard for what should have been recommended.”
  This is a construct-validity inference from an ED-encounter sample, not a measured estimate of missing community cases. ED disposition is not the proposed three-action ground truth.
- **qualified** (G_MIMIC; MIMIC_ED, MIMIC_TRIAGE): “Before scoring, have clinicians convert a held-out sample of de-identified presentations into concise symptom vignettes and independently assign one of three recommended actions: emergency care now, prompt appointment, or self-care.”
  A new adjudicated evaluation is explicitly proposed. It must constrain inputs to information available at presentation and retain the stated ED-sample limitation; the official dataset does not already supply these gold labels.
- **supported** (G_BOUNDARY; scope/inference): “This supports a conclusion about comparative performance on the adjudicated test cases, not proof of safer real-world outcomes.”
  Appropriate logical boundary of the proposed offline comparison; this is methodological reasoning rather than a claimed empirical result.

### H04 — heldout_nq_real_query_extraction_positive

- **supported** (G_NQ_RESOURCE; NQ_README, NQ_PAPER): “Use **Natural Questions (NQ)**, an English question-answering benchmark built from real Google Search queries, paired with Wikipedia pages and human annotations.”
  Direct resource applicability supported.
- **supported** (G_NQ_RESOURCE; NQ_README): “NQ includes short answer spans, yes/no answers, and cases where the supplied page has no annotated answer.”
  All listed annotation types exist. No-answer is an annotation/task state, not proof of universal absence.
- **supported** (G_NQ_RESOURCE; NQ_README, NQ_PAPER): “Use the public development set, which has multiple annotations per example.”
  The original development set has five annotations per example.
- **supported** (G_NQ_SCORE; NQ_EVAL, NQ_UTIL): “Use the **official NQ short-answer evaluator**: report precision, recall, and F1, following its rules for multiple spans, yes/no responses, acceptable annotations, and annotator agreement about answerability.”
  Correctly identifies the official scoring family and answerability concerns.
- **qualified** (G_NQ_SCORE; NQ_EVAL): “Each system should provide an answer confidence so its abstention threshold can be selected on the tuning portion and then frozen.”
  Sound fixed-threshold design, but the evaluator’s standard reporting reoptimizes F1 over supplied evaluation predictions. Use prethresholded predictions/fixed-threshold computation, and distinguish that from best-threshold benchmark F1.
- **supported** (G_BOUNDARY; scope/inference): “It would not measure retrieval quality, prove that declined questions have no answer elsewhere, or establish general factual accuracy beyond this setting.”
  Appropriate logical boundary of the proposed offline comparison; this is methodological reasoning rather than a claimed empirical result.

## Access failures and unresolved evidence

- [https://github.com/google-research-datasets/natural-questions/blob/fb26a3073b1fe636c97302890a27b491d6530130/README.md](https://github.com/google-research-datasets/natural-questions/blob/fb26a3073b1fe636c97302890a27b491d6530130/README.md): Web DisabledError. Successfully fetched identical pinned repository file via GitHub connector; blob recorded.
- [https://www.bmj.com/content/351/bmj.h3480](https://www.bmj.com/content/351/bmj.h3480): Direct web open returned 403 Forbidden. Primary publisher search-index content obtained; no direct full-page snapshot claimed.
- [https://pmc.ncbi.nlm.nih.gov/articles/PMC4496786/](https://pmc.ncbi.nlm.nih.gov/articles/PMC4496786/): Browser-check page, no article body. Primary BMJ indexed article and PubMed search abstract support core resource definition.
- [https://pubmed.ncbi.nlm.nih.gov/26157077/](https://pubmed.ncbi.nlm.nih.gov/26157077/): Direct open yielded only HHS footer. Search result returned abstract; not used to verify full supplemental case list.
- [https://www.bmj.com/content/351/bmj.h3480/suppl/DC1](https://www.bmj.com/content/351/bmj.h3480/suppl/DC1): Inaccessible via web tool. Adult subset unenumerated.
- [https://www.bmj.com/content/bmj/suppl/2015/07/08/bmj.h3480.DC1/semh022605.ww1.pdf](https://www.bmj.com/content/bmj/suppl/2015/07/08/bmj.h3480.DC1/semh022605.ww1.pdf): Initially guessed supplement path was inaccessible. Not treated as a verified artifact URL; later discovered cited canonical supplement attempted separately.
- [https://www.bmj.com/content/bmj/suppl/2015/07/07/bmj.h3480.DC1/semh025489.ww1.pdf](https://www.bmj.com/content/bmj/suppl/2015/07/07/bmj.h3480.DC1/semh025489.ww1.pdf): 403 Forbidden. Canonical supplement path discovered in later primary/secondary citations; contents and adult count remain unresolved.
- [https://pmc.ncbi.nlm.nih.gov/articles/PMC4496786/bin/bmj.h3480.ww1.pdf](https://pmc.ncbi.nlm.nih.gov/articles/PMC4496786/bin/bmj.h3480.ww1.pdf): Inaccessible via web tool. Plausible mirror filename not verified; not evidence of absent data.
- [https://europepmc.org/articles/PMC4496786](https://europepmc.org/articles/PMC4496786): Inaccessible via web tool. No source-content inference made from this failure.
- [https://www.nature.com/articles/s41597-022-01899-x](https://www.nature.com/articles/s41597-022-01899-x): 500 / publisher identity redirect inaccessible. Same primary paper retrieved on PMC, including clinical cohort definition.
- [https://mimic.mit.edu/docs/iv/modules/ed/edstays/](https://mimic.mit.edu/docs/iv/modules/ed/edstays/): Inaccessible path. Official versioned PhysioNet page provided disposition schema.
- [https://github.com/MIT-LCP/mimic-iv-website](https://github.com/MIT-LCP/mimic-iv-website): Two guessed documentation paths returned GitHub 404. No absence claim made; official web documentation was available.

The original assistants’ retrieval self-reports remain unresolved without access to their logs. Independent confirmation of page contents does not confirm a particular earlier browsing action. No source-access failure is treated as proof a resource does not exist.

This is a research-methodology audit. No clinical advice or deployment-safety conclusion is supplied.
