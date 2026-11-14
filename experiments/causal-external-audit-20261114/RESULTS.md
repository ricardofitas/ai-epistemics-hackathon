# Shared causes and a prospective MMMLU contract prediction

14 November 2026. Private research result.

Two shared implementation repairs explain input-construction failures across previously observed benchmark contracts. A prediction fixed before acquiring MMMLU source rows then succeeded on the selected 100 French MMMLU records. The public external-use investigation found an additional component execution log. An externally reported conclusion affected by the identified faults remains unverified.

## Causal diagnosis

The frozen study used 633 previously captured source records across seven panels and six intervention conditions. These produce 3,798 condition records. The intervention changes input construction while preserving the original locked native method bodies, the formatter and the local recording sink. It uses the previously documented AST dependency scaffold. No model endpoint or tokenizer was executed.

| Previously observed panel | Native result on selected records | Effect of the isolated repair |
| --- | --- | --- |
| WinoGrande | Question dependence absent on 100/100 | Binding the source sentence field to canonical question restores 100/100 |
| SciQ | Nonempty declared support omitted on 90/90 applicable records | Binding support to canonical context restores 90/90 |
| ARC-Challenge | Complete official choice sequence absent on 100/100 | Decoding parallel label/text lists restores 100/100 |
| OpenBookQA | Question dependence and complete choice sequence absent on 100/100 | The two shared repairs are jointly required to restore both |
| LAB-Bench | Official correct option absent on 33/33 | Both shared repairs leave this failure present. Explicitly adding ideal to distractors restores the complete option set |
| MedMCQA and MMLU controls | Question and option checks pass on 100 records each | All conditions preserve these measured properties |

The first cause is a mismatch between source-field names and the generator's available variables. The generator supplies question, context, choices and choices_text. Gallery templates can refer to sentence, question_stem, support or other source names. The formatter replaces supplied variables and leaves unsupported source symbols unresolved. Mapping the source question and context placeholders to canonical generator names restores the intended dependencies.

The second cause is the dictionary branch of the shared choice normalizer. For a dictionary containing parallel label and text lists, the native method sorts the keys and serializes both lists as separate answer choices. A decoder restricted to that validated structure restores the individual source choices. Ordinary choice lists and separate option columns pass the controls.

LAB-Bench provides a boundary case. Its configuration selects only distractors as the answer set. Input-symbol binding and dictionary decoding preserve that omission. Source-specific completion is required. This prevents a claim that one shared fix repairs every observed task.

The interventions concern the inputs. Reference parsing, scoring conventions and fixed correct-answer position remain separate issues.

## Prospective new native-contract prediction

The MMMLU protocol and implementation were committed before source-row acquisition. The implementation commit is d8597734749d2f8d0669c8114949e721b8d470b0, recorded at 12:30:41 UTC.

The default gallery selects MMMLU FR_FR/test. Its question field and template symbol are Question with a capital Q. The shared generator supplies the lower-case canonical question variable. The frozen prediction was that native question mutations would leave the delivered prompt unchanged, while the fixed source binding would restore dependence.

The official openai/MMMLU snapshot was pinned to 325a01dc3e173cac1578df94120499aaca2e2504. The exact file is test/mmlu_FR-FR.csv, containing 14,042 source records. Its SHA256 is 9e306e122e61513f2f0cdfae7eaceaaebac86e5bfa1ddbe63ec4e8562729ca50. The first 100 records in the frozen canonical-JSON SHA256 order were selected without substitution.

| Measured property | Native configuration | Fixed source binding |
| --- | --- | --- |
| Question affects the actual recorded prompt | 0/100 | 100/100 |
| Complete ordered source choices preserved | 100/100 | 100/100 |
| Official correct option present | 100/100 | 100/100 |
| Acquisition or execution errors | 0 | 0 |

A separate capture reconciliation, without loading the native renderer, verified every source record, the selection order, all option and answer mappings, and every captured prompt hash. For all 100 pairs, the repaired prompt is exactly the native prompt with the unresolved Question symbol replaced by the official question, retaining the formatter's surrounding braces.

This is a confirmed prediction on a new native configuration using a known fault mechanism. MMMLU translates MMLU, so the semantic questions may overlap the earlier English MMLU corpus. Gallery metadata had already been inspected. A global exposure census is unavailable. The evidence supports configuration transfer and the identified structural cause. It does not estimate fault prevalence or generalization to unseen mechanisms.

## External impact investigation

The earlier public search identified an external gallery consumer reporting a 19-model comparison. That consumer uses its own loaders and scorer and retains per-question records locally. The earlier affected-run criterion remained unresolved.

This iteration followed three additional primary leads.

| Lead | Primary evidence inspected | Scientific disposition |
| --- | --- | --- |
| Original One-Eval paper | Section 4.2 evaluates 100 requests through preparation and explicitly stops before model evaluation | Its 99/85/84 percent checkpoints do not provide original model-score traces for the affected configurations |
| Dataflow-LoopAI | Public one_eval.log records DataFlowEvalTool generation and evaluation for general_text_eval and gsm8k | Concrete component-use evidence outside the One-Eval repository. The log lacks the executable revision, affected-contract runs and a linked reported conclusion |
| Seed leaderboard file | The file header describes manually maintained reference scores with source papers, dates and settings | Reference scores offer no matching original One-Eval execution capture |

The LoopAI repository belongs to the same organization as One-Eval. The public log is evidence of component execution, with the limits of a released log. It does not establish independent replication.

Function-specific indexed searches added no matching external copy of the shared choice-normalizer class. A broader one_eval and winogrande query produced eight files. All eight blobs were inspected and matched generic function names or output path substrings, with no direct One-Eval import or explicit project reference. A project-reference plus eval_outputs query returned zero matches. These are bounded search outcomes.

The forks endpoint was rejected by the connector. The project homepage retrieval failed. Both errors are retained. Public missing artifacts cannot determine the frequency of affected private runs.

The strongest next external target remains a concrete original report or trace for an affected contract with the effective configuration and request/output evidence. An important affected conclusion could strengthen the comparison with GAMMAF. Its value depends on what the correction changes and how independently the evidence can be verified.

## Reproduction and provenance

Run the two commands below from this directory. The supplied captures and source selection are sufficient for offline verification. The root replay needs pandas and numpy.

```bash
python audit_shared_causes.py
python verify_captures.py
```

run_mmmlu_transfer.py records acquisition and execution. Running it again downloads the pinned source and replaces the local derived transfer files. Preserve the supplied originals before such a rerun.

The verification is a separate source/capture reconciliation performed by the same executor. Scientific review by another researcher remains open. The source archives, protocol commits, framework revision and upstream file hashes are recorded in EXECUTION_RECEIPT.json, INPUT_PROVENANCE.json and UPSTREAM_HASHES.json.

The source files come from Apache-licensed One-Eval and DataFlow components. The supplied MMMLU card identifies its MIT license. Original license files are retained.

[Original native preprocessing](https://github.com/OpenDCAI/One-Eval/blob/8aba20ad17ee2c7d2391162ac03ffaebcbb17506/one_eval/toolkits/dataflow_eval_tool.py) · [Official MMMLU snapshot](https://huggingface.co/datasets/openai/MMMLU/tree/325a01dc3e173cac1578df94120499aaca2e2504) · [One-Eval paper](https://arxiv.org/html/2603.09821v1) · [LoopAI runtime log](https://github.com/OpenDCAI/Dataflow-LoopAI/blob/30d078f36bb95508088f0ea229cbd804105b41f9/examples/scripts/one_eval.log)

