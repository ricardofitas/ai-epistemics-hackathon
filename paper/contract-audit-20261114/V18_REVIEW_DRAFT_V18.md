# C21/C22 review of working manuscript v1.8

Verdict: core claims PASS, with the minor precision edits below recommended before delivery. The previously identified UnifiedQA-small explicit-only rounding error has been corrected in the current JSON: 935 / 7,686 = 12.16%. I did not modify the manuscript, its claim ledgers or verifier. This review covers the new C21/C22 narrative, abstract/conclusion framing, Appendices J/K and their verification logic, without re-reviewing C1–C20.

## Confirmed

- All four new JSON evidence snapshots are semantically identical to the corresponding reports independently fetched during the earlier review at research commit 74f2aaf31f0f64c61f8d9efff29e995f43c04a59 (archive) and 1d39e5fbab209159f09b8b1573d89f78e47c8f8e (blind reading). Each recorded EVIDENCE_SOURCES.json SHA-256 matches its local snapshot bytes. The upstream PromptPG test/prediction blob ledger is retained.
- Independently recomputing the comparisons from all ten baseline counts, rather than trusting the supplied inversion lists, yields zero strict inversions after explicit-only recognition and precisely two after explicit recognition plus residual-zero abstention: pretrained TAPEX base versus pretrained UnifiedQA small/base.
- All twelve displayed Appendix J percentages match their displayed counts over 7,686 after the rounding correction. The original and qualified endpoint distinctions are clear. The 557 flags are correctly separated from 432 source questions; 397 gains plus 160 losses sum to 557.
- The 76,860 flags and 19,920 multiple-choice selections have the right repeated-observation denominators. The 100-case free-response endpoint comparison remains explicitly limited to that panel.
- C22's table matches the report: credited 40/2/7/1; uncredited 42/3/5/0. Planned tasks/terminals/complete responses are 224/224/223. Two readers each pass 12 controls; 99 study pairs are complete. Neither 224 nor 223 is represented as a question or pair denominator in the claim ledger.
- The main prose and qualifications correctly leave headline GPT-3/PromptPG results untested, separate TabMWP from MixEval/One-Eval mechanisms, label residual abstention as a scoring policy, and avoid human-validation or population-prevalence claims. General novelty and comparative superiority are not claimed. The ongoing 3,200-slot and 192-slot studies are not incorporated as completed evidence.

## Recommended small text edits

1. Appendix K first paragraph: replace **“These 224 model judgments”** with **“These 224 planned reader tasks”** or **“These 224 terminal reader records”**. One task does not yield a complete judgment, as the next paragraph correctly explains.
2. Appendix K execution paragraph: replace **“six explicit 429 refusals”** with **“six HTTP 429 rate-limit responses”**. The recorded field is http_429; this is transport/rate-limit accounting, not six substantive model refusals.
3. Appendix K human-reader paragraph: **“no invitations or external communications were sent”** is stronger than the inspected pinned report, which establishes no human responses collected. Retain that statement only if a separate execution/communications record actually supports it; otherwise use **“No human responses have been collected.”** It is unnecessary to the scientific claim.
4. Optional wording precision in abstract/Section 12: **“recognizing uniquely matching normalized options”** is narrower than **“unambiguous option recognition”**. The operational rule is uniqueness after Unicode/case/whitespace normalization; semantic unambiguity has not been established by humans. Appendix J already defines the actual operation, so this is a clarity improvement rather than a numerical defect.
5. Optional provenance precision: **“a separately implemented archive replay”** communicates the established sense of independence more directly than **“an independent archive replay”**, which some readers may interpret as a separate investigator or independent replication study. The report establishes a distinct implementation, not a newly executed replication by this reviewer.

## Verifier review

The current verifier checks the main aggregate counts, both exact inversion identities, credited-stratum labels, controls and snapshot hashes. Those checks are consistent with the pinned sources. It does not yet validate the Appendix J rendered table arithmetic or the Appendix K uncredited-stratum row; that is why a table rounding discrepancy could survive despite a passing claim verification.

Recommended targeted additions are (a) reconstruct all 45 pairwise inversion outcomes from the ten original/alternative integer counts; (b) bind each displayed Appendix J integer to the corresponding baseline/condition and derive its percentage at display precision; (c) assert the full first_wrong dictionary and 50-row sum for each blind stratum; (d) assert attempts = terminals + http_429 = 230. These are meaningful cross-representation checks. They do not require any new model/provider calls or broad old-claim revalidation.

The local review scripts independently performed (a), the displayed-percentage portion of (b), and comparison of all four new snapshots against separately fetched sources. All passed. This review checks aggregate evidence and narrative consistency; it does not rerun the underlying archive or audit raw provider terminals.
