# Source-only audit of the prospective P1 gap replication

This audit reads only the pinned source questions/solutions and the two independent first source reviews. It reports no solver-performance result, and no solver output was read. The source selection preplan was remotely frozen at `5706a87932ff33786f3c8dbdb69d6566532967ce` before first review assignments. The later study freeze and runtime files are not modified by this note.

## Admission and scope

The pool contains all **50 previously unused released Apple P1 source families**, excluding every family from the earlier 50-family P1/P2 review pool, including its rejected and uncertain families. Each candidate has GSM-Plus numerical substitution and a separate paraphrase, plus Apple P1 instances 0 and 1. These are two P1 realizations, **not P1/P2**, and the two target variants are separate examples rather than composed transformations.

Both first reviews passed **35 families**. The frozen rule selected the first **30** pass/pass families in seeded SHA256 priority order. **15 families** were excluded because at least one complete first review was reject or uncertain; **five eligible families** remained unused because they occurred after the quota (`P046`–`P050`). No uncertain judgment was overridden and no source question or gold value was edited. The review-pair counts are 35 pass/pass, 10 reject/reject, 3 uncertain/uncertain, 1 pass/uncertain and 1 uncertain/pass. Neither 15 exclusions nor 10 double rejections is a count of proven wrong-gold families.

The preserved first-review file SHA256 values are:

- A: `9857013cb30289321c503e1dd2ec4353428c67c5a95cc528291dcca155b4f467`
- B: `8d3c82d786d7b8f77dec3c8d1dce8a35945444ea6c63ac19aed20700716f9599`

See `admitted_source30/source_disposition.json` for all 50 first-review dispositions and `admitted_source30/SOURCE_GATE_RECEIPT.json` for the unchanged selected cohort (receipt SHA256 `73d6e60e73ea73a979d8c601c65fdae878bdec99ff13e26b6596215b2361bd5d`).

## Four independently rechecked contradictions

All four witnesses below occur in official GSM-Plus v1 at revision `3b708db57b96a16e8e3368ed2956990c0809440e`, file [data/test-00000-of-00001.jsonl](https://huggingface.co/datasets/qintongli/GSM-Plus/blob/3b708db57b96a16e8e3368ed2956990c0809440e/data/test-00000-of-00001.jsonl). Its whole-file SHA256 is `885c279bfa9cde767ea23f79fd462d566fa0dbf6af9f2dcf30c75aa94f3d4041`. Indices are zero-based; row hashes cover the exact UTF-8 JSON line without its line terminator. This audit independently checked each row hash, exact question, unchanged final answer, source solution and rational derivation against both first reviews.

| Review / family | Variant | Row | Released final answer | Derived answer | Derivation |
|---|---|---:|---:|---:|---|
| P024 / GSM8K-1247 | numeric | 9976 | 15 | **20** | `20×(1−1/4)+7−2 = 20` |
| P029 / GSM8K-718 | numeric | 5744 | 4 | **8** | `200×0.40×0.30/3 = 8` |
| P044 / GSM8K-858 | numeric | 6864 | 3430 | **300** | `12×(1+4)^2 = 300` |
| P012 / GSM8K-652 | paraphrase | 5221 | 75 | **105** | `15+30+60 = 105` |

### P024: exact released question

> Brendan has a bag of marbles with 20 inside. He tripped over a pebble while carrying it and dropped a quarter of them. He scrambled to search for them but only came up with 7. When he went back home, he inspected the marbles further. Two of them he picked up weren't marbles, but actually beads so he got rid of them. How many marbles did Brendan end up with?

Row SHA256: `bf09b1e1a5df8b5a1a0f249373f33478fa2bd2de94fc5385fd5e90cabfbb69c2`.

The retained marbles are 15; seven recovered objects include two beads, leaving five genuine recovered marbles. The released solution incorrectly uses half the initial bag instead of the stated quarter.

### P029: exact released question

> 200 people apply for a job at Google. Of the people that apply, only 40% receive interviews. Of those who receive interviews, 30% receive a job offer. Of those who receive a job offer, a third of the people accept the position. How many people accept the position?

Row SHA256: `aa36ae55f315a8041034948eeffcc0900961c275610e889946e6ad6255b712f8`.

There are 80 interviews, 24 offers and eight acceptances. The released solution labels the first multiplication as `200×0.40` but evaluates it as 40, then propagates that error.

### P044: exact released question

> A plague infects twelve people. Every day, each infected person infects four others. How many people are infected after two days?

Row SHA256: `bf319537eb3b42f431b94fc59bc72a6959dc00b7a3dc95bf58458988767c976c`.

Retaining infected people and adding four new infections per infected person gives a daily multiplier of five. The released solution itself derives 300 immediately before the inconsistent final-answer marker 3430. Thus the stored rationale and final answer also conflict internally.

### P012: exact released question

> James rents a horse carriage from 5 in the evening until 9 at night. He is not charged for the first hour. The initial hour that he pays for costs $15, and every subsequent hour is priced at double the previous hour's cost. What is the total amount that he had to pay?

Row SHA256: `13445944c1d6d9c5fd9fb98e4875c13b0971361b1891a2cce5fc8945e7d2cec1`.

The paraphrase explicitly says double the previous hour, so three paid hours cost 15, 30 and 60. Its retained solution instead prices every later hour at 30. The original seed and P1 wording leave the reference price ambiguous; the explicit paraphrase is the direct answer contradiction.

## Other exclusions and interpretation

Other concerns remain distinct from the four direct contradictions: unstated rounding or truncation (`P022`, `P041`), fractional people or item counts (`P010`, `P043`), whole-dozen purchasing assumptions and changed time units (`P018`), ambiguous running/walking ratios (`P003`), weekend allocations (`P006`), four-week-month conventions (`P014`), unlinked comet-sighting dates (`P015`) and contextual feasibility (`P017`). Their first-review dispositions are retained rather than promoted into arithmetic-error claims. P012's P1 realizations also retain ambiguity between repeated price growth and a fixed multiple of the first paid hour.

These findings concern a restricted, nonrandom source-linked pool screened for this experiment. They establish specific inconsistencies at the pinned release, **not novelty, benchmark-wide prevalence, or their persistence in later versions**. No source authors were contacted. The reviews and this audit are by independent agents rather than external human certification; shared-model mistakes remain possible. Source admission was based only on first reviews and the frozen quota, with no solver-output feedback.
