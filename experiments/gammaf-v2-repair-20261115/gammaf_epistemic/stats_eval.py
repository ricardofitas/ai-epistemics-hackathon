"""Statistical inference for detector comparisons.

The resampling unit is the *question*, not the debate: each question contributes
four topology debates, and those are not independent samples.  Within a task we
average the four graphs, then resample question IDs with replacement and average
the tasks with equal weight, mirroring the audit protocol.
"""

from __future__ import annotations

from typing import Mapping, Sequence

import numpy as np
from scipy import stats

from .data import TASKS, TOPOLOGIES, Debate


def split_questions(
    debates: Sequence[Debate], fraction: float = 0.2, seed: int = 20261112
) -> tuple[set[tuple[str, int]], set[tuple[str, int]]]:
    """Task-stratified question split used for hyperparameter tuning."""
    rng = np.random.default_rng(seed)
    tune: set[tuple[str, int]] = set()
    for task in TASKS:
        ids = sorted({d.item for d in debates if d.dataset == task})
        if not ids:
            continue
        take = max(1, int(round(fraction * len(ids))))
        chosen = rng.permutation(len(ids))[:take]
        tune.update((task, ids[i]) for i in chosen)
    everything = {(d.dataset, d.item) for d in debates}
    return tune, everything - tune


def question_scores(
    debates: Sequence[Debate], correct: Mapping[tuple, bool]
) -> dict[tuple[str, int], float]:
    """Mean correctness over the four topologies, per question."""
    buckets: dict[tuple[str, int], list[bool]] = {}
    for debate in debates:
        buckets.setdefault(debate.question_key, []).append(bool(correct[debate.key]))
    return {question: float(np.mean(values)) for question, values in buckets.items()}


def align(
    a: Mapping[tuple[str, int], float], b: Mapping[tuple[str, int], float]
) -> dict[str, np.ndarray]:
    """Per-task paired differences ``a - b`` over shared questions."""
    shared = sorted(set(a) & set(b))
    out: dict[str, list[float]] = {task: [] for task in TASKS}
    for question in shared:
        out[question[0]].append(a[question] - b[question])
    return {task: np.asarray(values, dtype=float) for task, values in out.items() if values}


def bootstrap_ci(
    diffs_by_task: Mapping[str, np.ndarray],
    *,
    n_boot: int = 10_000,
    seed: int = 20261112,
) -> dict:
    """Paired-question bootstrap over the equal-task-weighted mean difference."""
    tasks = sorted(diffs_by_task)
    arrays = [np.asarray(diffs_by_task[t], dtype=float) for t in tasks]
    rng = np.random.default_rng(seed)
    draws = np.zeros((n_boot, len(arrays)))
    for column, values in enumerate(arrays):
        index = rng.integers(0, len(values), size=(n_boot, len(values)))
        draws[:, column] = values[index].mean(axis=1)
    overall = draws.mean(axis=1)
    per_task = {}
    for column, task in enumerate(tasks):
        per_task[task] = {
            "mean_pp": 100.0 * float(arrays[column].mean()),
            "ci_low_pp": 100.0 * float(np.quantile(draws[:, column], 0.025)),
            "ci_high_pp": 100.0 * float(np.quantile(draws[:, column], 0.975)),
            "questions": int(len(arrays[column])),
        }
    return {
        "mean_pp": 100.0 * float(np.mean([values.mean() for values in arrays])),
        "ci_low_pp": 100.0 * float(np.quantile(overall, 0.025)),
        "ci_high_pp": 100.0 * float(np.quantile(overall, 0.975)),
        "resamples": int(n_boot),
        "per_task": per_task,
    }


def wilcoxon_holm(p_values: Mapping[str, tuple[float, float]]) -> dict[str, dict[str, float]]:
    """Two-sided Wilcoxon signed-rank tests with Holm-Bonferroni correction.

    ``p_values`` maps a comparison label to ``(statistic, p)``.
    """
    ordered = sorted(p_values.items(), key=lambda item: item[1][1])
    m = len(ordered)
    adjusted: dict[str, dict[str, float]] = {}
    running = 0.0
    for rank, (label, (statistic, p)) in enumerate(ordered):
        factor = m - rank
        running = max(running, min(1.0, p * factor))
        adjusted[label] = {
            "statistic": float(statistic),
            "p_value": float(p),
            "p_holm": float(running),
            "rank": rank + 1,
        }
    return adjusted


def paired_comparison(
    reference: Mapping[tuple[str, int], float],
    other: Mapping[tuple[str, int], float],
    *,
    n_boot: int = 10_000,
    seed: int = 20261112,
) -> tuple[dict, tuple[float, float]]:
    """Bootstrap interval plus Wilcoxon test for ``other - reference``."""
    diffs = align(other, reference)
    boot = bootstrap_ci(diffs, n_boot=n_boot, seed=seed)
    pooled = np.concatenate([diffs[t] for t in sorted(diffs)])
    if np.allclose(pooled, 0.0):
        statistic, p = 0.0, 1.0
    else:
        result = stats.wilcoxon(pooled, zero_method="wilcox", alternative="two-sided")
        statistic, p = float(result.statistic), float(result.pvalue)
    return boot, (statistic, p)


def holm_table(comparisons: Mapping[str, tuple[float, float]]) -> dict[str, dict[str, float]]:
    return wilcoxon_holm(comparisons)


def accuracy_percent(values: Sequence[bool]) -> float:
    return 100.0 * float(np.mean(values)) if len(values) else 0.0

