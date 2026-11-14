"""Epistemic audit, clean standard and detector for the GAMMAF benchmark.

Modules
-------
``data``            archived debate access (11,200 terminal decisions + trajectories)
``gammaf_clean``    the five ``GAMMAF-Clean`` measurement invariants
``audit_proofs``    false-credit theory, Monte Carlo and shadow contamination
``epistemic_guard`` the training-free graph-epistemic detector and soft aggregator
``stats_eval``      paired question bootstrap and Wilcoxon/Holm inference
"""

from .data import (
    CONTROL,
    DETECTORS,
    METHODS,
    N_AGENTS,
    N_INSIDERS,
    OPTION_SPACE,
    TASKS,
    TASK_LABELS,
    TOPOLOGIES,
    Debate,
    Round,
    Slices,
    handoff_dir,
    in_slice,
    load_debates,
    released_target_from_seed,
    schema_report,
    slice_counts,
    slices_of,
)
from .gammaf_clean import (
    ABSTAIN,
    REFERENCE,
    Delivery,
    Scored,
    canonical_option_labels,
    check,
    counterfactual_audit,
    deliver,
    detection_credit,
    discrepancy_table,
    patch_attack_sampler,
    empty_eligible_behavior,
    plurality,
    released_attack_sampler,
    releases,
    score_debate,
    stratification_summary,
)

__all__ = [
    "ABSTAIN",
    "CONTROL",
    "DETECTORS",
    "METHODS",
    "N_AGENTS",
    "N_INSIDERS",
    "OPTION_SPACE",
    "REFERENCE",
    "TASKS",
    "TASK_LABELS",
    "TOPOLOGIES",
    "Debate",
    "Delivery",
    "Round",
    "Scored",
    "Slices",
    "canonical_option_labels",
    "check",
    "counterfactual_audit",
    "deliver",
    "detection_credit",
    "discrepancy_table",
    "empty_eligible_behavior",
    "handoff_dir",
    "in_slice",
    "load_debates",
    "patch_attack_sampler",
    "plurality",
    "released_attack_sampler",
    "released_target_from_seed",
    "releases",
    "schema_report",
    "score_debate",
    "slice_counts",
    "slices_of",
    "stratification_summary",
]

__version__ = "0.1.0"

