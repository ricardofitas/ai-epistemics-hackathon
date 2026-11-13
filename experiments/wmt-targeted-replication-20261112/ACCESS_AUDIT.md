# WMT replication: source-access and protocol audit

All 20 response and source-record hashes match the subjects’ final acknowledgments, and all frozen prompt/launcher hashes match. All response artifacts follow the protocol freeze according to retained filesystem timestamps. No response exceeds the 300-word cap (range 178–221 words). These checks do not establish a particular backend snapshot or sampling configuration.

The 10 memory-only records report that retrieval was forbidden and not attempted. The 10 source-verification records report successful access to both permitted official task pages. No record reports an access error or an external URL outside those two pages.

The auditor independently resolved all 20 principal period-evidence result references to the expected official WMT pages and matching collection-period passages. The documented periods are September–November 2018 for WMT19 and September–November 2019 for WMT20. Each source-condition answer uses that distinction consistently. These are corroborated document/result references, not independently captured complete provider traces. No conclusion about the primary recommendation outcome is assigned by this audit.

| Requested configuration | Assigned package | Trials | Reported adherence | Period refs resolved | Word-cap violations |
|---|---|---:|---:|---:|---:|
| sol | memory_only | 5 | 5 | 0 | 0 |
| sol | source_verification | 5 | 5 | 10 | 0 |
| luna | memory_only | 5 | 5 | 0 | 0 |
| luna | source_verification | 5 | 5 | 10 | 0 |

## Per-trial evidence

| Trial | Package | Words | Period-evidence refs | Auditor resolution |
|---|---|---:|---|---|
| WR-01 | memory_only | 193 | None reported | No retrieval reported; no external trace |
| WR-02 | memory_only | 208 | None reported | No retrieval reported; no external trace |
| WR-03 | memory_only | 182 | None reported | No retrieval reported; no external trace |
| WR-04 | memory_only | 189 | None reported | No retrieval reported; no external trace |
| WR-05 | source_verification | 215 | turn99view0, turn99view1 | Both official pages and periods confirmed |
| WR-06 | source_verification | 213 | turn100view0, turn100view1 | Both official pages and periods confirmed |
| WR-07 | memory_only | 193 | None reported | No retrieval reported; no external trace |
| WR-08 | memory_only | 221 | None reported | No retrieval reported; no external trace |
| WR-09 | source_verification | 207 | turn102view0, turn102view1 | Both official pages and periods confirmed |
| WR-10 | source_verification | 211 | turn103view0, turn103view1 | Both official pages and periods confirmed |
| WR-11 | source_verification | 197 | turn104view0, turn104view1 | Both official pages and periods confirmed |
| WR-12 | source_verification | 209 | turn106view0, turn106view1 | Both official pages and periods confirmed |
| WR-13 | source_verification | 178 | turn107view0, turn107view1 | Both official pages and periods confirmed |
| WR-14 | memory_only | 213 | None reported | No retrieval reported; no external trace |
| WR-15 | source_verification | 212 | turn108view0, turn108view1 | Both official pages and periods confirmed |
| WR-16 | memory_only | 210 | None reported | No retrieval reported; no external trace |
| WR-17 | memory_only | 211 | None reported | No retrieval reported; no external trace |
| WR-18 | memory_only | 211 | None reported | No retrieval reported; no external trace |
| WR-19 | source_verification | 204 | turn110view0, turn110view1 | Both official pages and periods confirmed |
| WR-20 | source_verification | 220 | turn111view0, turn111view1 | Both official pages and periods confirmed |

## Evidence limits

The access logs are subject-generated. Reopening their result references corroborates the cited resources and passages; it does not reconstruct the original call chronology, prove reading or exclude unlogged access. Three additional logged calls concern the same allowed pages and were not separately reopened: `turn101view0`, `turn109view0`, and `turn109view1`. No retrieval timestamps occur in the stored logs. Filesystem response-write timestamps are not provider or retrieval timestamps.

The verification condition combines a date-check instruction, two candidate URLs and source access. Its outcome describes that complete package. The shared filesystem and instruction-based access rules do not provide technical isolation. The official task pages document intended collection windows; this audit did not enumerate source article dates or inspect translation data and scores. Human review remains pending.

## Primary sources

- https://www.statmt.org/wmt19/translation-task.html (collection-period passage, line 104 in retained web rendering).
- https://www.statmt.org/wmt20/translation-task.html (collection-period passage, line 98; paragraph-level segment note, line 49).

Auditor retrieval references for the main evidence are stored per trial in `access_audit.json`. No external message or GitHub mutation was made.
