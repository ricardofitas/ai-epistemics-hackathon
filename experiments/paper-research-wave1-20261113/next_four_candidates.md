# Four proposed source-case families for the next breadth screen

Prepared 13 November 2026. **Proposal only: zero subject calls and zero newly tested families.** The parent reports a 21-family inventory; this review did not inspect the current wave’s outputs/ratings or independently reverify its outcome count. Four completed future case families could bring that inventory to 25. The existing frozen wave and primary rubric remain unchanged.

Selection uses missing construct/domain coverage, not adverse previews. All anchors below are evaluator-side examples; the proposed user questions contain no benchmark names or answer facts. Source-defined facts were checked against the linked primary/official pages on the date above. Data-byte download and scorer execution were not performed.

| Candidate | Added coverage | Status |
|---|---|---|
| Probabilistic weather forecasting on unseen years | Physical spatiotemporal forecasting, ensemble distributions, lead-time dependence and temporal validation | source verified candidate freeze pending |
| Causal treatment effects and interval accuracy | Counterfactual causal estimands, identification assumptions and interval coverage, rather than factual prediction or another question-answering score. | source verified candidate freeze pending |
| Offline continuous-control policy return | Offline sequential decision learning, action-induced distribution shift and policy value | source verified candidate version pin pending |
| Image-and-language object localization | Multimodal language-to-region grounding and geometric output scoring | provisional data delivery and scorer pin |

## 1. Probabilistic weather forecasting on unseen years

**Proposed user question**

> I’m comparing two ensemble weather models that issue temperature forecasts one to ten days ahead. Which public data and scoring setup would let me compare the quality of their predictive distributions on years not used for training, and what would a stronger result justify?

**Construct:** Out-of-time predictive-distribution skill for temperature, evaluated at stated forecast lead times on a common held-out period and verification target.

**Why new:** Physical spatiotemporal forecasting, ensemble distributions, lead-time dependence and temporal validation; distinct from language-model confidence calibration and translation source-year fit.

**Anchors and availability:** WeatherBench 2 public datasets; WeatherBench-X evaluation framework. Public cloud catalog and baseline/verification datasets documented; no dataset bytes downloaded in this proposal. Official code and CRPSEnsemble API available; pin framework revision, ensemble treatment and aggregation before a performance experiment.

**Fair source-fit notes for later review/freeze:**

- Accept an aligned public weather dataset or a justified alternative with a temporally held-out period and an appropriate predictive-distribution score such as CRPS.
- An ensemble-mean RMSE comparison can support a point-forecast claim; alone it does not establish comparative quality of the full predictive distribution.
- Accept a carefully bounded retrospective claim. Do not require proof of all future-year behavior, a particular region, an extreme-event test or every calibration metric, because the question does not request them.
- Do not declare a resource invalid merely because it is older if the proposed evaluation uses appropriate unseen years and states the supported time scope.

**Risks and valid adaptations:**

- Match lead times, initialization conditions, grid, variable and verification target; ERA5 reanalysis and operational analyses are not automatically interchangeable.
- A probabilistic forecast adapter can be valid if specified and validated; deterministic models may be compared on a separately bounded point-forecast target.
- Global average skill does not imply skill in every region or season. Source/version details are reviewer checks, not automatic failure for every omitted detail.

**Primary/official sources:** [WeatherBench-X official documentation](https://weatherbench-x.readthedocs.io/en/latest/); [WeatherBench official data guide](https://weatherbench2.readthedocs.io/en/latest/data-guide.html); [WeatherBench-X official metrics API](https://weatherbench-x.readthedocs.io/en/latest/api/metrics.html); [WeatherBench official FAQ](https://sites.research.google/gr/weatherbench/faq/).

**Before the next freeze:** Pin dated source snapshots and exact question. Review the interpretation of probabilistic skill and bounded temporal claims; keep extremes outside required criteria.

## 2. Causal treatment effects and interval accuracy

**Proposed user question**

> I’m comparing methods that estimate how much a program changes outcomes for the people who received it, using observational data. What public evaluation data and scoring procedure would let me compare the accuracy of those effect estimates and their uncertainty? Explain what conclusion the comparison would support.

**Construct:** Accuracy and interval uncertainty of the sample average treatment effect among the treated (SATT) in observational settings with known simulated potential outcomes.

**Why new:** Counterfactual causal estimands, identification assumptions and interval coverage, rather than factual prediction or another question-answering score.

**Anchors and availability:** ACIC 2016 SATT competition; aciccomp2016 author R data/simulation package. Organizer release includes potential outcomes and author R package is documented; no package/data installed here. Target and error/coverage calculations are specified; exact simulation release and local scoring implementation need pinning before performance work.

**Fair source-fit notes for later review/freeze:**

- Accept semisynthetic or simulated observational data with a known treated-population effect and aligned effect-error and uncertainty evaluation; do not require the ACIC name.
- Factual observed-outcome prediction RMSE alone cannot establish treatment-effect accuracy; it can be a supporting diagnostic or qualified proxy.
- A real observational dataset without counterfactual ground truth can support assumption-dependent causal and sensitivity analyses, not a claim that effect error was directly observed.
- Do not require individual/CATE estimates, every organizer metric or real-world program-effect proof: the intended target is the average effect among treated sample members.

**Risks and valid adaptations:**

- Separate sample SATT from population ATT/ATE and individual effects; an explicit conversion or appropriately changed bounded target can be valid.
- ACIC simulations assume measured-confounder ignorability. They do not automatically test hidden-confounding robustness or establish real program effectiveness.
- Use the released/corrected source version and keep potential outcomes evaluator-only when assessing an estimator; the recommendation subject receives no source answer key.

**Primary/official sources:** [ACIC 2016 organizers competition definition and release](https://jenniferhill7.wixsite.com/acic-2016/competition); [ACIC author data and simulation repository](https://github.com/vdorie/aciccomp); [Automated versus do-it-yourself methods for causal inference](https://arxiv.org/abs/1707.02641).

**Before the next freeze:** Pin organizer release and author package revision. Have a causal-methods-capable reviewer confirm the SATT target, counterfactual truth and interval criteria.

## 3. Offline continuous-control policy return

**Proposed user question**

> I’m comparing policies learned entirely from a fixed log of continuous-control trajectories. What public data and evaluation procedure should I use to compare how much reward the trained policies earn when they control the matching simulator? Explain what conclusion the comparison would support.

**Construct:** Expected episodic return of a new policy in a specified simulator when training is restricted to fixed offline data; evaluation rollouts are allowed by the question.

**Why new:** Offline sequential decision learning, action-induced distribution shift and policy value; distinct from ScienceWorld textual goal completion or browser workflow success.

**Anchors and availability:** D4RL-family datasets through Minari; Concrete optional anchor: D4RL/door/human-v2 with its documented AdroitHandDoor-v1 environment. Minari documents the fixed dataset download; no trajectories downloaded in this proposal. Matching environment can be recovered; sum episode rewards for raw return, with normalized scores optional only when valid reference metadata exists.

**Fair source-fit notes for later review/freeze:**

- Accept fixed-log training and evaluation of trained-policy returns from fresh matching simulator episodes with the stated environment/reward version.
- Raw episodic return is acceptable. A normalized score is optional, and the source dataset reference metadata must govern any normalization.
- Accept another verified offline-control suite. A justified off-policy evaluation estimate may be accepted with explicit assumptions and coverage limits; do not reject every non-rollout approach.
- Held-out action prediction, behavior-cloning loss or the logged behavior policy’s reward alone does not establish the learned policy’s achieved return.
- Do not require a particular algorithm, seed count or install command. Simulator evaluation is not additional training interaction merely because the learning setting is offline.

**Risks and valid adaptations:**

- Current Minari D4RL-family reproductions are not all identical to legacy D4RL; use a named dataset/environment/reward version, not cross-version leaderboard equivalence.
- The concrete door dataset specifies dense reward and a 200-step horizon; do not infer its reward from a generic domain description.
- Simulator return does not establish physical-robot transfer or safe deployment. Offline support/coverage assumptions matter for off-policy estimates.

**Primary/official sources:** [D4RL primary paper](https://arxiv.org/abs/2004.07219); [Official Minari D4RL-family catalog](https://minari.farama.org/datasets/D4RL/index.html); [Official Minari basic usage](https://minari.farama.org/content/basic_usage/); [Official Minari normalized-return utility](https://minari.farama.org/api/minari_functions/); [Official Minari D4RL/door/human-v2 dataset specification](https://minari.farama.org/datasets/D4RL/door/human-v2/).

**Before the next freeze:** Pin exact dataset and environment specifications or explicitly keep recommendations benchmark-level only. Have an offline-RL-capable reviewer check that fresh evaluation rollouts and qualified off-policy estimates are fairly accepted.

## 4. Image-and-language object localization

**Proposed user question**

> We’re comparing two systems that take a photograph and a short expression identifying one object, then return a bounding box. What public evaluation data and scoring setup should we use to measure how reliably they locate the intended object in new photographs, and what conclusion would a better score support?

**Construct:** Referring-expression comprehension: localization of the described object by bounding-box accuracy against grounded annotations on image-disjoint evaluation data.

**Why new:** Multimodal language-to-region grounding and geometric output scoring; distinct from ImageNet-C image classification robustness and text-only role-sensitive NLI.

**Anchors and availability:** RefCOCOg UMD image-disjoint split; RefCOCO UNC image-disjoint splits as a valid alternative. Annotations and COCO-image requirements are documented; original author server is marked broken and catalog requires manual data. Current mirror bytes/provenance have not been checked. Primary paper specifies bounding-box IoU > 0.5 accuracy; author evaluation tooling exists but uses old Python requirements. Exact UMD-compatible scorer and threshold convention remain to be pinned.

**Fair source-fit notes for later review/freeze:**

- Accept annotated referring-expression grounding data and direct localization scoring, including a verified alternative dataset or an explicitly aligned custom image-disjoint test.
- Accept suitable IoU-based accuracy or another justified geometric correctness rule; do not make the curator’s exact threshold a hidden mandatory requirement.
- Generic caption fluency, image-text similarity or image-level retrieval alone is not direct evidence of returning the correct object box. Such measures may remain qualified diagnostics.
- A known-proposal ranking evaluation is valid for a bounded comprehension claim; an end-to-end box-output claim must include the proposal/localization step or clearly qualify the scope.
- Do not reject all Google splits as useless: object-disjoint results can be reported accurately, but they alone do not establish the question’s new-photograph target when train/test images overlap.

**Risks and valid adaptations:**

- RefCOCOg Google and UMD splits differ; do not merge their scores or treat Google validation as a canonical UMD test.
- Bounding boxes, masks and object-proposal settings are distinct tasks. Accept valid adapters if their outputs and claims align.
- Operational source work remains: verify official-linked mirror provenance, data licenses and IDs, and a scorer adaptation on hand-checked boxes before freezing a decisive source key.

**Primary/official sources:** [Author referring-expression dataset API](https://github.com/lichengunc/refer); [Official TensorFlow Datasets RefCOCO catalog](https://www.tensorflow.org/datasets/catalog/ref_coco); [Modeling Context in Referring Expressions, primary paper](https://arxiv.org/abs/1608.00272); [Author Google Refexp evaluation toolbox](https://github.com/mjhucla/Google_Refexp_toolbox).

**Before the next freeze:** Resolve annotation delivery from an author-linked source and pin image/split IDs. Pin and independently check a modern compatible localization scorer and threshold boundary. Have a grounding-capable reviewer check image-disjointness and proposal-versus-end-to-end scope; keep this slot provisional if unresolved.

## Planned stage and review capacity

**One S0 breadth screen:** four cases × four previously declared configuration slots × one fresh request = **16 planned attempts**, after a separate source/payload freeze. No new models are selected here. Recurrence, wording transfer, evidence interventions and actual benchmark-performance runs are outside this block. Only the question plus common response instructions/settings is model-facing. Retain all four labels and operational failures; accept verified alternatives and qualified proxies under the unchanged primary rule. A source-family count increases only after an interpretable recommendation exists, with its review status visible.

**Review workload:** two fresh anonymous first agent ratings per completed answer, at most 32 first ratings. Reserve human capacity for four source/construct cards and at most 16 answers: every claimed material failure, each disputed/uncertain scope, and a prespecified reproducibly selected aligned/qualified answer per family when available. The reviewer assignment has not been confirmed. One human validates only that scope; two independent humans on a declared subset would permit an agreement claim. If capacity is limited, stage or defer cards and keep claims pending, rather than accumulating unreviewed breadth.

**Provisional slot:** image-and-language localization has strong primary construct/split/scoring support, but current annotation delivery and a compatible scorer need verification before its decisive source key is frozen. It remains a proposed fourth slot, not a tested family. All other slots still need ordinary version/snapshot and exact-payload freezes.

**Paper claim bound:** the screen would document advice on four curated scientific-evaluation problems. One answer per configuration does not establish error rates, robustness, a benchmark bug, actual downstream harm or model rankings. Report aligned advice and nulls as fully as material failures.
