# Rig research results, 23 November 2026

The updated ICML preprint includes the minimax proofs, runnable samplers and matched benchmark comparisons. [Paper and certificates](../../campaign/option-order-design-20261122/icml-draft/README.md)

[Machine-readable aggregate results](aggregate-results.json)

- **Evaluation.** These results cover the original local Qwen2.5 1.5B and Granite 3.3 2B quantized pair. On SciQ (480 items), the Williams point reduction versus precedence minimax was 1.75%, with an inconclusive 5% practical-margin decision. On ARC-Easy (480 items), the point reduction was −0.36%. The paired bootstrap and normal-family intervals rule out a 5% practical gain against precedence minimax on that panel. The Hoeffding sensitivity remains inconclusive. The SciQ validation split remained closed. The HellaSwag bootstrap uses previously released predictions and adds no new inference.
- **MetaXFam.** On five development families, the canonical endpoint used 60.0% of the four-phase CPU time and reduced vector error 8.22% versus the strongest measured-affordable high-only comparator. Vector error was 1.02% higher than four-phase, above the fixed 1% noninferiority margin. The matched-cost gain ranged from 4.9% to 17.0% with each family omitted in turn. These diagnostics describe the development panel. Confirmation families remained sealed.

Only aggregate evidence is included. The analysis contains no question-level predictions, answer keys, materials tensors, or holdout outcomes.
