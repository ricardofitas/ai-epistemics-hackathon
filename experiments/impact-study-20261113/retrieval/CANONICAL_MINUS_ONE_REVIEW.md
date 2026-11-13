# Canonical minus-one qrel review

**Pass:** the pinned canonical scorer treats a negative relevance label as an unjudged pool entry. The two official residual-qrels rows with -1 remain unchanged; their source hash is recorded in the JSON receipt.

At official trec_eval v10.0 commit f4253652c8efd0d86ddffd0d163cc0a0f813111a, README line 100 documents the sentinel. The input conversion in form_res_rels.c distinguishes an unjudged pool entry from a document absent from the pool, while the normal scoring path retains both at their ranked positions. nDCG counts only positive gain; P@10 counts only labels meeting the default relevance threshold.

A generated two-topic fixture was scored three ways: its unjudged entries labelled -1, the same entries absent from qrels, and the same entries labelled 0. Canonical stdout was byte-identical for the declared ndcg_cut.10 and P.10 metrics. Exact fixture bytes, output text, hashes, source blob hashes and line warrants are preserved in CANONICAL_MINUS_ONE_REVIEW.json and the synthetic_minus_one folder. No actual candidate run or comparative outcome was evaluated.

The equivalence is scoped to these two metrics under the declared flags, which do not enable judged-only ranking. It is not a license to discard ranked unjudged documents, globally relabel source data, or assume all other metrics ignore pool distinctions.

The appropriate correction is to accept and preserve the official -1 sentinel in the preflight validator and pass the exact original qrels to the canonical scorer. The parent owns the evaluator/protocol correction and a transparent new freeze before actual scoring. This is our source-validation correction, not a discovered benchmark defect. This review did not modify the evaluator, protocol, scorer or official source data.
