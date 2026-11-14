# Source-contract mutation diagnostics

The unchanged v1 checker was structurally inspected, then protocol and experimental v2 wrapper were frozen before execution at commit 796d95065d41007655afae8e713c89199dcfe905. This is a development diagnostic, not independent validation.

The study uses 200 previously observed official MMLU/MMLU-Pro source records and 11 controlled conditions per record: 2,200 variants. A synthetic renderer, not a new native-framework execution, produces the visible question and labelled options. Mutation probes are recomputed through the same renderer. No provider/model calls or source acquisition occurred.

| Condition group | Variants | v1 accepted | v2 accepted |
|---|---:|---:|---:|
| Identity, edge trimming, coherent option permutation | 600 | 600 | 600 |
| Distractor replacement/removal, duplicated gold, partial question | 800 | 800 | 0 |
| Question omitted, gold removed, wrong reference | 600 | 0 | 0 |
| Missing source evidence | 200 | 200 | 0 |

The final group is INCOMPLETE in v2 and blocks the constructed backend. All accepted cases invoked only a local counting function, never a model. The 2,200 variants are repeated transformations of 200 source units and must not be interpreted as independent natural failures or a detection prevalence estimate.

A separate source-bound wrapper adds a full source-question substring check and exact normalized option multiset preservation, including multiplicities, while retaining v1 gold/reference checks. It permits coherent permutations and edge trimming. The original checker is unchanged.

After the synthetic results, an explicitly recorded development replay applied unchanged v2 to the already observed 27,346 remaining natural records. It preserved the prior decision in all four panels: reject ARC-Challenge (1,072) and OpenBookQA (400), accept MMLU (13,942) and MMLU-Pro (11,932). This is regression evidence on observed data, not a new independent holdout.

## Limits

v2 still trusts the adapter's source anchors, displayed-choice metadata and measured probes. It does not parse arbitrary prompt layouts to establish that reported choices are the actual displayed choices, establish cryptographic source provenance, or prove that question text is semantically used merely because it occurs in the prompt. Its performance beyond these design cases remains unmeasured. No score change, model ranking reversal, real-world deployment frequency or externally affected evaluation is claimed.

The natural One-Eval faults previously established remain distinct from these deliberately introduced mutations and from weaknesses of our own audit tool.

## Reproduction

Requires only standard-library Python and the prior OneEval_extensao_splits_completos_20261114.zip, SHA-256 3c9d248d83d9c4318a121f52074a6eea8de83136da7510b0ad816d5aa36e4ae2. Extract that archive as BASE:

    python run_mutations.py BASE
    python verify_mutations.py BASE
    python replay_natural.py BASE

The included inputs, full per-variant reports, summaries, natural replay, protocol and exact checker source are sufficient to inspect all claims. Running the scripts replaces only local result files in this package. No network or model endpoint is called.

Next: reconcile the existing paired-model trial and resource ledger; then freeze a genuinely new evaluator/source validation instead of repeatedly expanding the same development cases.

