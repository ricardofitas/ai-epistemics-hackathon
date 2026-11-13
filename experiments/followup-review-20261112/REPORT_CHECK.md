# Independent prepublication report check

**Passed after one factual correction.** The final report now gives the verified mapping **WR-01→R12, WR-02→R18, WR-03→R10, WR-04→R02, WR-07→R16**, consistent with both `review_key.jsonl` and `summary.json`. The prior “respectively” list misassociated four trials. Counts and labels were unaffected. The final example names WR-01.

The 20 WMT completions and balanced cell counts (Luna memory 5/5, other cells 0/5), all four holdout no labels, integrity/timing descriptions, and 28 blank/pending human judgments agree with retained records. The report correctly bounds source access as an instruction-plus-candidate-source package and preserves the null archive result, missing fourth model, and weight/reference provenance limits. No original ratings were altered and no new subjects were run.

The feasibility-report Markdown link is correct relative to `docs/experiments/wmt-targeted-replication-results.md`. Reproduction materials are repository-root paths shown as code, not clickable relative links. If converted to links, use `../../experiments/...`, `../../scripts/...`, and `WMT_HUMAN_REVIEW.md`; source-audit links would use `../../experiments/wmt-targeted-replication-20261112/ACCESS_AUDIT.md` and `access_audit.json` in that directory.

The final independent factual audit supports the source-period and NQ provenance conclusions. Literal “one hypothesis per sentence” instructions in R01/R09 conflict with paragraph reference units; the audit records this factual limitation while the original primary reviewers did not infer an actual misaligned run or a further material failure. Keep that distinction transparent without rewriting first ratings. No additional substantive correction is required.
