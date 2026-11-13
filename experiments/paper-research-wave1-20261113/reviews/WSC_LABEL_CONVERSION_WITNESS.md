# Authentic WSC label-conversion witness

The official SuperGLUE v2 release contains one Mark/Pete passage with a negative coreference record for Pete and a positive companion record for Mark. Its labels concern the referent of **He**. They are not official three-way NLI labels.

> Mark told Pete many lies about himself, which Pete included in his book. He should have been more truthful.

| Released record | Target candidate | Target pronoun | Official coreference label |
|---|---|---|---|
| `WSC/train.jsonl`, line388, `idx=387` | Pete | He | false |
| Same passage, line459, `idx=458` | Mark | He | true |

Source: [official SuperGLUE v2 WSC.zip](https://dl.fbaipublicfiles.com/glue/superglue/data/v2/WSC.zip). Downloaded 2026-11-13T04:56:22.573804+00:00. Release path: `v2`; Last-Modified: `Tue, 09 Jul 2019 08:03:33 GMT`; S3 version: `exaynVEK8XkamvIqEM.luZE4JYpVpuZ6`.

Archive: 32751 bytes, SHA256 `2ed6dfa94556b4a128ff0441efe365b2e883124e7e6aa00fb8d3a6cb1fd520a9`. `WSC/train.jsonl`: 140984 bytes, SHA256 `0ffaa3fd8d21e58a0805962565d1619aa4819bc3d034255777f606f801ae5a42`. Exact raw JSON lines and their individual hashes are preserved in the companion JSON file. The URL is a release URL rather than a Git commit; the recorded hashes identify the fetched bytes.

The audited Q48 rule is “hypothesis 2 = replacement by the non-gold entity, labeled contradiction.” Applying it would replace the marked **He** by **Pete** and assign contradiction.

A counterworld preserves the official referent **Mark**: Mark lies to Pete, Pete includes those lies in a book, and Mark should have been more truthful. In addition, Pete knowingly includes a separate fabricated story and therefore also should have been more truthful. The original passage says nothing that rules out this additional wrongdoing by Pete. Both the gold-resolved premise and the Pete-replaced sentence can thus be true together. The premise does not entail the negation of the Pete-replaced sentence, so the automatic contradiction label does not follow.

This is an analyst-created compatibility argument. It does **not** assert an official neutral label, entailment of the non-gold sentence, an observed classifier error, a model-ranking change, or a dataset-wide failure rate. The authentic coreference labels remain unchanged. Human review is pending.

The [SuperGLUE primary paper](https://proceedings.neurips.cc/paper_files/paper/2019/file/4496bf24afe7fab6f046bf4923da8de6-Paper.pdf), §3.2, defines this binary coreference task. [Ernest Davis’s author collection](https://cs.nyu.edu/~davise/papers/WS-11-27), item61, independently corroborates the Mark/Pete schema; the recorded dataset labels and hashes above come directly from the official release.
