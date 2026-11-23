# Matched 3B HellaSwag extension of the Four Orders experiment

Freeze a third panel of 992 questions using HellaSwag validation (Rowan/hellaswag revision 218ec52e09a7e7462a5400043bb9a69a41d06b76). Use the exact two pinned Q4_K_M model files, tokenizer, standard numeric question-and-options prompt, 512-token admission rule, eight-slot native decoder and physical RTX 4060 Ti from the 992-item MMLU and LogiQA runs. Map HellaSwag's ctx to the Question field and its four endings to the Options field. Preserve context case and option content. There are 47,616 full-order reference calls and 7,936 calls at deployment budget, each across both models.

The initial label-free screen tested previously unused validation items
and found 765 qualifying questions under both model tokenizers. Because
992 are required, retain those items and fill the remaining slots from
the previously released 6,144-item HellaSwag panel, which ran different
models and a different prompt. Select the supplemental items without reading
inference outputs, correctness or labels. The earlier 192-item reserve and
48-item development roster stay excluded by source ID and normalized context.
Require unambiguous keys and contexts and four distinct nonempty endings.
Apply the same 1,450-character screen and under-512-token admission rule
used for the 3B study. Order fresh candidates and supplemental candidates
by fixed SHA-256 hashes. Process fresh candidates first, then up to the first
1,536 supplemental candidates, and stop at 992 jointly qualified rows.
Use the publisher's in-domain and zero-shot strata with fixed observed
weights for resampling. Report the mix by origin and stratum. The resulting
cohort represents this screened HellaSwag panel.

Hash the full roster, fixtures, worker and protocol before dispatch. Keep scoring columns closed until a complete, eligible queue release and validate all prediction checkpoints first. Allow one checkpointed retry with the same fixtures and physical GPU. No selection, early stopping, movement of the 5-point decision threshold or expansion based on results.

Primary contrast is Williams versus precedence minimax at the original 5% practical MSE margin. Use the same exact four-order catalog, paired stratified bootstrap with 50,000 draws, 2.5th and 97.5th percentile bounds, and normal and bounded sensitivities. The extension has a single panel and leaves the original joint inference of MMLU and LogiQA unchanged. Report the exact MSE and point relative reduction for all designs, threshold crossing, ties, strict sign reversals and the adjacency, residual and interaction terms. Compare the three matched-setting point estimates and their panel-specific uncertainty descriptively. Report the new result regardless of sign; a sign change alone does not establish benchmark-wide superiority.
