# Targeted workflow provenance check

**No explicit archive/Complete mismatch was found in the inspected sample.** This is a bounded negative check, not evidence that no such workflow exists elsewhere. No model calls or comparative scoring were performed.

The existing Q55 and Q57 answers recommend evaluating the user’s retrieval components. Neither specifies archived submissions or a cumulative-qrels filename. Their observed statistical-equivalence error cannot be extended into a provenance error by assumption.

NIST distinguishes its Complete collection from the residual task used for official Round 5 submissions. The archived files already have previously judged documents removed. Replaying those files against Complete cumulative qrels would test a different protocol and cannot silently reproduce the shared-task evaluation. [Official data definitions](https://ir.nist.gov/trec-covid/data.html); [Round 5 qrels](https://ir.nist.gov/trec-covid/qrels5.html); [Archive](https://ir.nist.gov/trec-covid/archive.html).

The inspected Anserini implementation is a negative control. At commit `d69c77b43a5eb59a7e735b1b3a5438de8e14e567`, `generate_round5_baselines.py` evaluates Complete qrels with its `cumulative_runs` collection and Round 5 qrels with `final_runs`. Its documentation distinguishes original and NIST-postprocessed files. We did not identify the alleged combination there. [Pinned script](https://github.com/castorini/anserini/blob/d69c77b43a5eb59a7e735b1b3a5438de8e14e567/src/main/python/trec-covid/generate_round5_baselines.py).

Targeted searches used two engines, and exact source pins/snapshot hashes are recorded in the companion JSON files. Search snippets incidentally displayed some published Anserini aggregate scores; this scout must not be described as blind to all historical aggregates. No official score report, per-topic performance or comparison outcome was inspected or calculated, and those snippets were not used to select candidates.

The parent’s actual-run route should preserve the matching residual task. An intentionally wrong qrels replay would currently be a diagnostic only. A separate, prospective ordinary advice query about replicating official Round 5 scores could test whether assistants actually make the provenance mistake, but no such recommendation has been sampled here.
