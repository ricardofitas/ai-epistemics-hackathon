# Reproduce the SQuAD consequence check

Use Python 3 with the standard library. No provider credentials, model calls or judge calls are required.

1. Obtain the eight `contract-transfer-wave-*-43624040280` artifacts from the authenticated GitHub run in `ricardofitas/swarm-adaption-hackathon`, and the older native archive `14124236646` from run `43620987144`. Verify ZIP hashes in `ACQUISITION.json`. Extract each into `inputs/<artifact-name>/`; the older archive is `inputs/native-live/`. This study's analysis reads only the eight wave captures; native data is a separately retained boundary check.
2. Fetch the original SQuAD development source from `rajpurkar/SQuAD-explorer`, revision `240e165ab706d95bd4323653bb92421f446208cf`, path `dataset/dev-v1.1.json`, into `squad-dev-original.json`. Its Git blob must be `e9a3f913ad1468ebe105b891334ca7b0bc0e2510`.
3. Keep `cases.json`, `design.py` and `scoring.py` byte-identical to their pins. They came from `ricardofitas/ai-epistemics-hackathon` revision `290941f5392604b1943d95b6acf318f976c17ee6`, under `experiments/external-contract-transfer-20261114`.
4. Keep `official_squad_evaluate.py` byte-identical to Git blob `e60acfd1044319e43a59ffe8db75e63b68785ba7` from `huggingface/evaluate`, path `metrics/squad/compute_score.py`. The blob is the authority; do not silently replace it with a newer copy.
5. Run `python analyze_consequence.py`. It authenticates the original files and captures, executes the unchanged public metric, reproduces all completed primary exact-match labels, and writes the ledger, witness and summary.

The official scorer is a maintained copy of the SQuAD v1.1 evaluation script. The source repository snapshot used for the dataset does not itself contain `evaluate-v1.1.py`; this fact is retained rather than inventing a source path. The exact maintained scorer blob is supplied with the analysis.

`downloads.private.json` and `acquire.py` are local transfer intermediates and must not be published. Expiring signed URLs are not part of the scientific evidence. Large original artifacts and source data are reproducible dependencies; avoid duplicating all originals in a new repository commit.

The original generation experiment was prospective; this official-metric verification is retrospective and expected aggregate results were already exposed. A separate assistant independently verified source/capture bytes and arithmetic using `independent_agent_verify.py`; its result is in `INDEPENDENT_AGENT_VERIFICATION.json`. This is independent assistant verification, not independent human review or new model evidence.
