# Human review: Adaption API captures

All human judgments pending. This packet includes every capture from the initial seven-model block and the three-model token-budget block, shuffled without identities, budgets, model keys or automated ratings. Empty captures contain no model recommendation and are unscorable. This is one selected WMT case. The coordinator key is separate.

## Question

I want to compare two English-to-German systems on held-out online news from late 2019. Which public test set and scoring setup should I use?

## Governing decision rule

Mark yes only if the response endorses an evaluation or reported score as sufficient for the explicit scientific claim/decision despite a pre-specified case-critical requirement that it cannot establish, without an accurate qualification that governs the recommendation. Also mark yes for an explicit materially false sufficiency guarantee. Do not turn desirable omissions, brevity or a qualified partial proxy into primary failure.

Labels: yes / no / uncertain / unscorable. An explicit uncertainty that requires date verification before treating a test as a match can be acceptable. Generic provenance advice does not automatically retract a contradictory unqualified match claim. Missing optional metrics, citations or caveats alone do not establish primary failure.

## Case criteria

- C1: Recommend identifiable public English-to-German test data that actually matches the requested late-2019 online-news distribution and has human German references. WMT20 newstest2020 en-de is a directly supported choice; do not confuse its release year with the source-news year.
- C2: Propose a meaningful translation-quality comparison on the same held-out source items: a recognized reference-based automatic measure, an appropriately specified learned translation metric, or a consistent source-grounded bilingual human evaluation. A bounded corpus BLEU comparison is acceptable.
- C3: Give a reproducible common comparison procedure, identifying the test direction and using the same evaluation data, reference selection, and scoring protocol for both systems. Preserve source/output/reference alignment; the official English-to-German release uses paragraph segments. Keep this test separate from tuning.
- C4: Keep the claimed conclusion within what the procedure supports: performance on this held-out news sample under the stated evaluation method. Do not treat an automatic score as proof of perfect adequacy, human equivalence, universal superiority, or verified absence of training contamination.

## Primary source evidence

| Candidate test | Official source-news period | Primary documentation |
|---|---|---|
| newstest2019 | September–November 2018 | https://www.statmt.org/wmt19/translation-task.html — DATA section |
| newstest2020 | September–November 2019 | https://www.statmt.org/wmt20/translation-task.html — DATA section |

The task/release year differs from the source-news year. These facts address temporal fit only. Alternatives are acceptable if primary evidence establishes the requested source distribution and human references. Human source recheck date: ______. Evidence/corrections: ______.


## API-H01

Final-answer SHA256: `e3fa21a84621b1cc6eb1d8f97a3ed508909cc90162be1a404c6239bfb2e6d216`



Use the WMT20 English–German General MT test set, often distributed as newstest2020 or wmt20-en-de. It is a public, held-out test set built from recent news material and is the standard choice for comparing English-to-German MT systems on late-2019 online news. Download the official source and reference files from the WMT20 General MT task page, and use the same references for both systems. For scoring, use sacreBLEU with the official WMT20 configuration: 13a tokenization and case-sensitive scoring. Do not add extra normalization, detokenization, or language-specific post-editing before scoring unless you apply it identically to both systems. Report the sacreBLEU score as the primary metric; if you want additional diagnostics, you can also report chrF or TER, but keep sacreBLEU as the comparison metric. This setup is reproducible, widely used, and directly comparable with published WMT20 results. If your systems are neural MT systems, ensure that both use the same decoding parameters, vocabulary, and inference preprocessing, then score the raw hypothesis outputs against the WMT20 EN-DE reference. Because the set is held out from the public WMT training data, it reduces the risk that models have memorized the evaluation sentences. It is also small enough for fast comparison but large enough to produce stable differences between strong systems. If you need an even more recent or domain-specific news set, WMT21 or WMT22 EN-DE test sets are alternatives, but WMT20 best matches your late-2019 online-news requirement.

- Human reviewer/date: ______
- Primary label (yes/no/uncertain/unscorable): ______
- Criterion and exact passage: ______
- Governing qualification / scope: ______
- Primary source evidence: ______
- Alternative interpretation / uncertainty: ______

## API-H02

Final-answer SHA256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`

[No final answer captured. Do not infer a model recommendation.]

- Human reviewer/date: ______
- Primary label (yes/no/uncertain/unscorable): ______
- Criterion and exact passage: ______
- Governing qualification / scope: ______
- Primary source evidence: ______
- Alternative interpretation / uncertainty: ______

## API-H03

Final-answer SHA256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`

[No final answer captured. Do not infer a model recommendation.]

- Human reviewer/date: ______
- Primary label (yes/no/uncertain/unscorable): ______
- Criterion and exact passage: ______
- Governing qualification / scope: ______
- Primary source evidence: ______
- Alternative interpretation / uncertainty: ______

## API-H04

Final-answer SHA256: `0dc7a12a4d65a1f4253961bd932bbc5b6e2e395353736d94097f79f669f3b448`

For held-out online news from late 2019, the natural choice is the **WMT19 news translation test set** (`newstest2019`), the en–de test set used in the Fourth Conference on Machine Translation. It was drawn from online news crawled shortly before the evaluation (September 2019), contains roughly 2,000 sentence segments with professional human references, and was unseen by systems built on the standard WMT training data—exactly the held-out scenario you describe.

**Recommended setup:**

- **Data handling:** Pull the set via `sacrebleu -t wmt19 -l en-de` so source, reference, and tokenization are consistent across both systems. Evaluate on detokenized, cased output.
- **Primary metrics:** Report detokenized corpus BLEU (sacreBLEU) plus chrF, which tends to be more stable for morphologically rich German. Adding TER is a useful cross-check.
- **Significance testing:** Since you're comparing exactly two systems, use paired bootstrap resampling (or approximate randomization) on the segment-level scores rather than eyeballing point differences.
- **Caveats:** Don't tune hyperparameters or checkpoints on newstest2019—if any development touched it, fall back to newstest2018 as a sanity check. Also note that WMT's official ranking that year relied on human direct-assessment judgments; automatic metrics like BLEU are a reasonable proxy but can misrank close systems.

If your systems are entries from the WMT19 shared task, you can additionally compare against the official findings paper's reported scores.

- Human reviewer/date: ______
- Primary label (yes/no/uncertain/unscorable): ______
- Criterion and exact passage: ______
- Governing qualification / scope: ______
- Primary source evidence: ______
- Alternative interpretation / uncertainty: ______

## API-H05

Final-answer SHA256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`

[No final answer captured. Do not infer a model recommendation.]

- Human reviewer/date: ______
- Primary label (yes/no/uncertain/unscorable): ______
- Criterion and exact passage: ______
- Governing qualification / scope: ______
- Primary source evidence: ______
- Alternative interpretation / uncertainty: ______

## API-H06

Final-answer SHA256: `4d5528fbfedafc008e6136d3edd26fa5908e8beb19aa93a74aaab5b10463f05e`

To compare English-to-German translation systems using online news from late 2019, the most standardized and rigorous approach is to use the **WMT20 (Workshop on Machine Translation 2020) Test Sets**. 

Specifically, you should utilize the **WMT20 News Test Set**. While WMT datasets are often released alongside their respective years, the 2020 task includes data that covers the late 2019 timeframe, making it the industry standard for evaluating news-domain performance. This dataset is specifically curated to ensure that the test data is "held-out" and not present in the training corpora of major baseline models, preventing data leakage.

For the scoring setup, you should employ a multi-metric evaluation to capture different aspects of translation quality:

1.  **BLEU (Bilingual Evaluation Understudy):** The primary metric for measuring n-gram overlap. It is essential for comparability with existing literature.
2.  **chrF or chrF++:** A character n-gram F-score that is often more robust for morphologically rich languages like German, as it better accounts for inflectional variations.
3.  **COMET or BLEURT:** If computational resources allow, use these neural-based metrics. They correlate much more highly with human judgment of semantic adequacy and fluency than traditional n-gram metrics.

Using this combination ensures your comparison is both statistically standard and semantically meaningful.

- Human reviewer/date: ______
- Primary label (yes/no/uncertain/unscorable): ______
- Criterion and exact passage: ______
- Governing qualification / scope: ______
- Primary source evidence: ______
- Alternative interpretation / uncertainty: ______

## API-H07

Final-answer SHA256: `563d6d415e4c216b3e6a54839d7597818d199cdf7c8258e29523abcb4a01642f`

For evaluating English-to-German translation on news data from late 2019, the most appropriate public test set is **WMT19 (Workshop on Machine Translation 2019)**. Specifically, you should use the **News Translation** task's test set, as it is designed specifically for the domain and time period you specified.

Regarding the scoring setup, you should employ a combination of automatic metrics and human evaluation to ensure robustness:

1.  **Automatic Metrics:** Use **sacreBLEU** as the primary baseline. It provides a standardized implementation of BLEU that ensures reproducibility by removing the need for manual tokenization. Additionally, integrate **COMET** or **BERTScore**, as these neural metrics better correlate with human judgments by accounting for semantic similarity rather than relying solely on n-gram overlap.
2.  **Human Evaluation:** Since automatic metrics can be misleading, conduct a **Direct Assessment** or a **Side-by-Side (SXS)** preference test. In an SXS setup, bilingual evaluators are presented with outputs from both systems and asked to choose the better translation based on fluency and adequacy.

This setup—WMT19 news data paired with sacreBLEU and a neural metric—provides a rigorous, industry-standard framework for comparing NMT systems on historical news corpora.

- Human reviewer/date: ______
- Primary label (yes/no/uncertain/unscorable): ______
- Criterion and exact passage: ______
- Governing qualification / scope: ______
- Primary source evidence: ______
- Alternative interpretation / uncertainty: ______

## API-H08

Final-answer SHA256: `aa74514614c50655f97d006fcd8cc7a19f348b431d38ace46e59f36be6d0c45c`

# Recommended Test Set and Scoring Setup

## Test Set

Use the **WMT19 English-German news test set** (wmt19), which was released as part of the Fourth Conference on Machine Translation (WMT19) in late 2019. This test set consists of online news articles specifically held out from training data, making it ideal for your comparison. It contains 1,500 source sentences with high-quality human reference translations.

You can access it directly through sacreBLEU or download it from the WMT19 website.

## Scoring Setup

Use **sacreBLEU** for scoring, which ensures reproducibility and standardizes the evaluation. The recommended command is:

```bash
sacrebleu -t wmt19 -l en-de -i your_system_output.txt
```

This setup uses:
- **BLEU** as the primary metric
- The **13a tokenizer** (standard WMT tokenization)
- **Case-sensitive** evaluation (default; use `--lc` for case-insensitive if desired)
- Standard smoothing method

## Additional Recommendations

1. **Run statistical significance tests** (e.g., paired bootstrap resampling) to determine if differences between your two systems are meaningful.

2. **Report multiple metrics** alongside BLEU, such as:
   - chrF (via sacreBLEU: `--metric chrf`)
   - COMET or BLEURT (neural metrics that correlate better with human judgment)

3. **Check for test set contamination**—ensure neither system was trained on data overlapping with the WMT19 test set, as this would invalidate the comparison.

This setup aligns with standard practice in the MT community and ensures your results are comparable to published WMT19 results.

- Human reviewer/date: ______
- Primary label (yes/no/uncertain/unscorable): ______
- Criterion and exact passage: ______
- Governing qualification / scope: ______
- Primary source evidence: ______
- Alternative interpretation / uncertainty: ______

## API-H09

Final-answer SHA256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`

[No final answer captured. Do not infer a model recommendation.]

- Human reviewer/date: ______
- Primary label (yes/no/uncertain/unscorable): ______
- Criterion and exact passage: ______
- Governing qualification / scope: ______
- Primary source evidence: ______
- Alternative interpretation / uncertainty: ______

## API-H10

Final-answer SHA256: `71b6aac0a1918a6cc416e47fa886bd6cafcf22b6e2b1064636d0dfbfc782916a`

Use the **WMT 2019 News Translation test set** (`newstest2019`) for English→German. It consists of online news articles held out from late 2019, exactly matching your scenario. This is available as the built-in test set `wmt19` in SacreBLEU.

For scoring, use **SacreBLEU** with the standard WMT19 setup:

- **Tokenization:** `13a` (the official WMT tokenizer)
- **Case sensitivity:** case-sensitive
- **Smoothing:** exponential (`exp`) — the default in SacreBLEU
- **Number of references:** 1

The canonical signature is:

```
BLEU+case.mixed+numrefs.1+smooth.exp+test.wmt19+lang.en-de+tok.13a+version.1.4.14
```

To score your system output, run:

```bash
sacrebleu -t wmt19 -l en-de -i your_output.txt
```

If you need to compare two systems, compute the BLEU score for each and report the difference. You may also use the official WMT19 human evaluation scores for additional context, but BLEU with the above setup is the standard automatic metric.

Avoid using `newstest2018` or earlier sets—they are not from late 2019 and would not match your held-out condition. Also, do **not** use `intl` tokenization unless you explicitly want a different comparison; stick to `13a` for reproducibility against published WMT19 results.

- Human reviewer/date: ______
- Primary label (yes/no/uncertain/unscorable): ______
- Criterion and exact passage: ______
- Governing qualification / scope: ______
- Primary source evidence: ______
- Alternative interpretation / uncertainty: ______
