#!/usr/bin/env python
"""Run every GAMMAF epistemic experiment and emit tables, JSON and figures.

Usage::

    python scripts/run_hackathon_experiments.py --out artifacts
    python scripts/run_hackathon_experiments.py --only guard --fast

Outputs (in ``--out``)::

    results.json              all numbers behind every table
    schema.txt                exact schema of the archived debate logs
    Table_Discrepancy.tex     released vs delivered score mismatch
    Table_DetectionCredit.tex padded-round vs executed-round ADR
    Table_Counterfactual.tex  substitution invariance audit
    Table_Stratification.tex  236 / 64 attack-target slices
    Table_FalseCredit.tex     detector FPR/TPR and false-credit calibration
    Table_Shadow.tex          pre-exclusion contamination
    Table_Leaderboard.tex     head-to-head delivered accuracy
    Table_Rollback.tex        epistemic rollback and rehabilitation ensemble
    Table_OracleParadox.tex   Oracle Paradox by attack-validity slice
    Table_OracleWithin.tex    oracle vs detector within each conversation set
    Table_Stats.tex           paired bootstrap and Wilcoxon/Holm
    fig_false_credit.png      false-credit rate vs detector FPR
    fig_leaderboard.png       held-out delivered accuracy
    fig_shadow.png            shadow contamination by topology
"""

from __future__ import annotations

import argparse
import collections
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping, Sequence

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from gammaf_epistemic import (  # noqa: E402
    CONTROL,
    DETECTORS,
    REFERENCE,
    TASKS,
    TASK_LABELS,
    TOPOLOGIES,
    counterfactual_audit,
    deliver,
    detection_credit,
    discrepancy_table,
    empty_eligible_behavior,
    in_slice,
    load_debates,
    releases,
    schema_report,
    score_debate,
    slice_counts,
    slices_of,
)
from gammaf_epistemic.audit_proofs import (  # noqa: E402
    decompose_oracle_paradox,
    detector_profiles,
    false_credit_curve,
    monotonicity_check,
    ORACLE_SLICES,
    oracle_delivery,
    oracle_flags,
    oracle_slice,
    shadow_summary,
    theorem_statement,
    tie_free_credit,
)
from gammaf_epistemic.epistemic_guard import (  # noqa: E402
    EnsembleParams,
    EpistemicGuard,
    GuardData,
    ensemble_result,
    rollback_delivery,
    tune_ensemble,
)
from gammaf_epistemic.stats_eval import (  # noqa: E402
    holm_table,
    paired_comparison,
    question_scores,
    split_questions,
)

GUARD_HARD = "EpistemicGuard-Hard"
GUARD_SOFT = "EpistemicGuard-Soft"
GUARD_ROLLBACK = "EpistemicGuard-Rollback"
ORACLE_ROLLBACK = "Oracle-Rollback"
GUARD_ENSEMBLE = "EpistemicGuard-Ensemble"
NO_DETECTOR = "No detector"
LEADERBOARD = [
    *DETECTORS,
    GUARD_HARD,
    GUARD_SOFT,
    GUARD_ROLLBACK,
    ORACLE_ROLLBACK,
    GUARD_ENSEMBLE,
    NO_DETECTOR,
]


# --------------------------------------------------------------------------- #
# Formatting helpers
# --------------------------------------------------------------------------- #
def print_table(title: str, headers: Sequence[str], rows: Sequence[Sequence]) -> None:
    print(f"\n{title}")
    data_rows = [row for row in rows if not (row and str(row[0]) == "MIDRULE")]
    width = [
        max(len(str(header)), *(len(f"{row[i]}") for row in data_rows))
        if data_rows
        else len(str(header))
        for i, header in enumerate(headers)
    ]
    print("  ".join(str(h).ljust(w) for h, w in zip(headers, width)))
    print("  ".join("-" * w for w in width))
    for row in rows:
        if row and str(row[0]) == "MIDRULE":
            print("  ".join("-" * w for w in width))
            continue
        print("  ".join(f"{value}".ljust(w) for value, w in zip(row, width)))


def tex(text: object) -> str:
    """Headers, captions and notes are authored LaTeX; data cells are plain."""
    return str(text)


def latex_table(
    path: Path,
    caption: str,
    label: str,
    headers: Sequence[str],
    rows: Sequence[Sequence],
    note: str | None = None,
    col_spec: str | None = None,
) -> None:
    spec = col_spec or ("l" + "r" * (len(headers) - 1))
    lines = [
        r"\begin{table}[htbp]",
        r"\centering",
        r"\small",
        rf"\caption{{{tex(caption)}}}",
        rf"\label{{{label}}}",
        rf"\begin{{tabular}}{{{spec}}}",
        r"\toprule",
        " & ".join(tex(h) for h in headers) + r" \\",
        r"\midrule",
    ]
    for row in rows:
        if row and str(row[0]) == "MIDRULE":
            lines.append(r"\midrule")
            continue
        lines.append(" & ".join(tex(value) for value in row) + r" \\")
    lines.extend([r"\bottomrule", r"\end{tabular}"])
    if note:
        lines.append(rf"\par\smallskip\footnotesize {tex(note)}")
    lines.append(r"\end{table}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_json(path: Path, payload: object) -> None:
    def default(value):
        if isinstance(value, (np.integer,)):
            return int(value)
        if isinstance(value, (np.floating,)):
            return float(value)
        if isinstance(value, np.ndarray):
            return value.tolist()
        if isinstance(value, set):
            return sorted(value)
        raise TypeError(f"not serialisable: {type(value)}")

    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=default) + "\n",
        encoding="utf-8",
    )


def mean_percent(values: Sequence[float]) -> float:
    return 100.0 * float(np.mean(values)) if len(values) else 0.0


# --------------------------------------------------------------------------- #
# Experiment 1: the clean standard
# --------------------------------------------------------------------------- #
def run_clean(debates, out: Path) -> dict:
    print("\n=== 1. GAMMAF-Clean invariants ===")
    discrepancy = discrepancy_table(debates)
    rows = []
    for task in TASKS:
        cells = discrepancy["by_task"].get(task, {})
        if not cells:
            continue
        debates_n = sum(c["debates"] for c in cells.values())
        released = sum(c["released_correct"] for c in cells.values())
        delivered = sum(c["delivered_correct"] for c in cells.values())
        rows.append(
            [
                TASK_LABELS[task],
                debates_n,
                released,
                delivered,
                sum(c["disagreements"] for c in cells.values()),
                sum(c["false_credits"] for c in cells.values()),
                sum(c["missed_credits"] for c in cells.values()),
            ]
        )
    totals = discrepancy["totals"]
    rows.append(
        [
            "Total",
            totals["debates"],
            totals["released_correct"],
            totals["delivered_correct"],
            totals["disagreements"],
            totals["false_credits"],
            totals["missed_credits"],
        ]
    )
    rows.append(["Disabled controls", discrepancy["controls"]["debates"], "-", "-",
                 discrepancy["controls"]["disagreements"], 0, 0])
    print_table(
        "Released vs delivered score (9,600 detector debates + 1,600 controls)",
        ["Task", "Debates", "g_rel", "g_del", "Disagree", "False credit", "Missed credit"],
        rows,
    )
    print(f"reference match (227/156/71, 0 control): {discrepancy['matches_reference']}")
    latex_table(
        out / "Table_Discrepancy.tex",
        "Released correctness versus delivered-answer correctness on the archived "
        "GAMMAF debates. Disagreements are concentrated in the 156 false credits.",
        "tab:discrepancy",
        ["Task", "Debates", "$g_{rel}$", "$g_{del}$", "Disagree", "False credit", "Missed credit"],
        rows,
        note="Controls raise no flag, so the two electorates coincide.",
    )

    empty = empty_eligible_behavior(debates)
    modes = [
        ["strict_abstain", "ABSTAIN", 0, "live-judge rule: abstention is wrong"],
        ["soft_fallback", "v[argmin s]", "check(a_del, y)", "requires suspicion scores"],
    ]
    print_table(
        f"Empty eligible set U = empty (archived cases: {empty['archived_cases']})",
        ["Mode", "a_del", "g_del", "Note"],
        modes,
    )

    credit = detection_credit(debates)
    credit_rows = []
    for task in TASKS:
        cell = credit["controls"].get(task)
        if not cell:
            continue
        credit_rows.append(
            [
                TASK_LABELS[task],
                cell["padded_rounds"],
                f"{cell['released_adr_percent']:.2f}",
                f"{cell['executed_adr_percent']:.2f}",
                f"{cell['phantom_percent']:+.2f}",
            ]
        )
    print_table(
        "Disabled-detector detection credit: released third round vs last executed round",
        ["Task", "Padded rounds", "Released ADR %", "Executed ADR %", "Phantom pp"],
        credit_rows,
    )
    print(f"phantom eliminated under executed-round accounting: {credit['eliminates_phantom']}")
    latex_table(
        out / "Table_DetectionCredit.tex",
        "Detection credit for the disabled controls. The released third-round ADR is "
        "manufactured by padded rounds imputed after convergence.",
        "tab:detection-credit",
        ["Task", "Padded rounds", "Released ADR (\\%)", "Executed ADR (\\%)", "Phantom (pp)"],
        credit_rows,
        note="The executed-round ADR is 0.00\\% in every task, which is the only "
        "value a detector that raises no flag can earn.",
    )

    audit = counterfactual_audit(debates)
    cf_rows = []
    for name, label in (
        ("paper1_insider", "Paper 1 insider"),
        ("exhaustive_option_space", "Exhaustive options"),
    ):
        universe = audit["universes"][name]
        for task in TASKS:
            counter = universe["by_task"].get(task, {})
            if not counter:
                continue
            cf_rows.append(
                [
                    label,
                    TASK_LABELS[task],
                    counter.get("substitutions", 0),
                    counter.get("g_del_changes", 0),
                    counter.get("release_flips", 0),
                    counter.get("debates_with_release_flip", 0),
                    counter.get("debates_with_release_flip_prior_flagged", 0),
                    "",
                ]
            )
        totals_cf = universe["totals"]
        cf_rows.append(
            [
                label,
                "Total",
                totals_cf.get("substitutions", 0),
                totals_cf.get("g_del_changes", 0),
                totals_cf.get("release_flips", 0),
                totals_cf.get("debates_with_release_flip", 0),
                totals_cf.get("debates_with_release_flip_prior_flagged", 0),
                "yes" if name == "paper1_insider" and universe["matches_paper1_reference"] else "",
            ]
        )
        cf_rows.append(["MIDRULE", "", "", "", "", "", "", ""])
    cf_rows.pop()
    print_table(
        "Counterfactual substitution invariance: Paper 1 universe vs exhaustive space",
        ["Universe", "Task", "Substitutions", "g_del changes", "g_rel flips",
         "Debates flipped", "Prior-round flags", "Matches P1"],
        cf_rows,
    )
    paper1 = audit["universes"]["paper1_insider"]
    print(
        f"Paper 1 rule reproduces 33,025 / 121 / 89: "
        f"{paper1['matches_paper1_reference']} "
        f"({paper1['totals'].get('substitutions')} subs, "
        f"{paper1['totals'].get('debates_with_release_flip')} flipped debates, "
        f"{paper1['totals'].get('debates_with_release_flip_prior_flagged')} with the "
        "insider flagged in the immediately preceding round)"
    )
    print(
        "invariance g_del(v,f) == g_del(v',f) for v_U == v'_U in both universes: "
        f"{audit['invariance_holds']} / "
        f"{audit['universes']['exhaustive_option_space']['invariance_holds']}"
    )
    latex_table(
        out / "Table_Counterfactual.tex",
        "Counterfactual substitution audit under both universes. Replacing an excluded "
        "insider vote never changes the delivered answer or its grade, but it moves the "
        "released score. The Paper 1 restricted universe is 33,025 substitutions over "
        "excluded insiders; the exhaustive space is 142,478 replacements over all labels.",
        "tab:counterfactual",
        ["Universe", "Task", "Substitutions", "$g_{del}$ chg", "$g_{rel}$ flips",
         "Debates", "Prior-round", "P1"],
        cf_rows,
        note="Prior-round counts substitutions whose insider was already flagged in the "
        "immediately preceding executed round. Both universes leave $g_{del}$ invariant; "
        "only the released score moves.",
        col_spec="llrrrrrl",
    )

    counts = slice_counts(debates)
    slices = slices_of(debates)
    strat_rows = []
    for name, questions in slices.names().items():
        members = [d for d in debates if d.method in DETECTORS and d.question_key in questions]
        scored = [score_debate(d) for d in members]
        strat_rows.append(
            [
                name.replace("_", r"\_"),
                counts[name]["questions"],
                len(members),
                f"{mean_percent([s.g_release for s in scored]):.2f}",
                f"{mean_percent([s.g_del for s in scored]):.2f}",
                sum(s.false_credit for s in scored),
                sum(s.missed_credit for s in scored),
            ]
        )
    print_table(
        "Attack-target stratification",
        ["Slice", "Questions", "Debates", "g_rel %", "g_del %", "False credit", "Missed credit"],
        strat_rows,
    )
    latex_table(
        out / "Table_Stratification.tex",
        "Dataset stratification induced by the released attack-target sampler: "
        "236 genuinely adversarial multiple-choice questions and 64 self-sabotaged ones.",
        "tab:stratification",
        ["Slice", "Questions", "Debates", "$g_{rel}$ (\\%)", "$g_{del}$ (\\%)",
         "False credit", "Missed credit"],
        strat_rows,
        note="GSM8K contributes 100 questions to TRUE\\_ADVERSARIAL\\_236; the numeric "
        "task is always genuinely adversarial because the sampler emits a letter.",
    )

    return {
        "discrepancy": discrepancy,
        "empty_eligible": empty,
        "detection_credit": credit,
        "counterfactual": audit,
        "stratification": {
            "counts": counts,
            "rows": strat_rows,
        },
    }


# --------------------------------------------------------------------------- #
# Experiment 2: false-credit theory
# --------------------------------------------------------------------------- #
def run_theory(debates, out: Path, *, n_sim: int, figure: bool) -> dict:
    print("\n=== 2. False-credit inflation ===")
    alphas = [0.0, 0.05, 0.1, 0.15, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7]
    curve = false_credit_curve(0.7, 0.2, alphas, n=n_sim)
    monotone = monotonicity_check(
        0.7, 0.2, alphas, n=max(n_sim // 2, 10_000)
    )
    bound = tie_free_credit(0.7, 0.3, 0.2)
    profiles = detector_profiles(debates, n_sim=n_sim)

    rows = []
    for name, cell in profiles["rows"].items():
        rows.append(
            [
                name,
                f"{cell['alpha']:.3f}",
                f"{cell['tpr']:.3f}",
                f"{cell['inflation_pp']:+.3f}",
                f"{cell['false_credits']}",
                f"{cell['missed_credits']}",
                f"{cell['predicted_false_credit_rate'] * 100:.2f}",
                f"{cell['observed_false_credit_rate'] * 100:.2f}",
            ]
        )
    print_table(
        "Detector false-positive rate, true-positive rate and false credit",
        ["Detector", "alpha", "TPR", "Inflation pp", "FC", "MC", "Pred FC %", "Obs FC %"],
        rows,
    )
    print(
        f"corr(alpha, observed FC) = {profiles['correlation_alpha_vs_observed_fc']:.3f}; "
        f"corr(predicted, observed) = {profiles['correlation_predicted_vs_observed']:.3f}; "
        f"MAE = {profiles['mean_absolute_error'] * 100:.2f} pp"
    )
    print(f"false credit nondecreasing in alpha at fixed TPR: {monotone['nondecreasing']}")

    def tied(values) -> bool:
        counts = collections.Counter(values).most_common()
        return len(counts) > 1 and counts[0][1] == counts[1][1]

    archive_fc = [
        d for d in debates if d.method in DETECTORS and score_debate(d).false_credit
    ]
    archive_mc = [
        d for d in debates if d.method in DETECTORS and score_debate(d).missed_credit
    ]
    tied_release = sum(tied(d.votes) for d in archive_fc)
    tied_eligible = sum(
        tied([d.votes[i] for i in d.eligible]) for d in archive_mc
    )
    print(
        f"tie-free enumeration at alpha=0.3, TPR=0.8: FC={bound.p_false_credit * 100:.2f}% "
        "(a uniform-distractor artefact that understates the evaluator)"
    )
    print(
        f"archive: {tied_release}/{len(archive_fc)} false credits and "
        f"{tied_eligible}/{len(archive_mc)} missed credits involve a tied tally, so "
        f"{len(archive_fc) - tied_release} false credits are unique-winner flips caused "
        "by expelling correct votes rather than by the tie rule"
    )
    latex_table(
        out / "Table_FalseCredit.tex",
        "Detector calibration against the false-credit model. $\\alpha$ is the honest-agent "
        "flag rate, TPR the insider flag rate; predicted FC is the model rate at the "
        "measured $(\\alpha,\\mathrm{TPR})$.",
        "tab:false-credit",
        ["Detector", "$\\alpha$", "TPR", "Inflation (pp)", "FC", "MC",
         "Pred. FC (\\%)", "Obs. FC (\\%)"],
        rows,
        note="The model is a structural illustration, not a calibrated predictor: the "
        "observed correlation is reported in the text rather than assumed. Only 26 of "
        "the 156 archived false credits have a tied released tally, so 130 are "
        "unique-winner flips caused by expelling correct votes.",
        col_spec="lrrrrrrr",
    )

    if figure:
        fig, axis = plt.subplots(figsize=(6.4, 4.2))
        for p_h, style in ((0.6, ":"), (0.7, "-"), (0.8, "--")):
            rates = false_credit_curve(p_h, 0.2, alphas, n=n_sim)
            axis.plot(
                alphas,
                [r.p_false_credit * 100 for r in rates],
                style,
                marker="o",
                markersize=3,
                label=f"$p_h$={p_h}",
            )
        axis.scatter(
            [cell["alpha"] for cell in profiles["rows"].values()],
            [cell["observed_false_credit_rate"] * 100 for cell in profiles["rows"].values()],
            marker="x",
            color="black",
            s=28,
            label="observed detectors",
        )
        for name, cell in profiles["rows"].items():
            axis.annotate(
                name,
                (cell["alpha"], cell["observed_false_credit_rate"] * 100),
                fontsize=6,
                xytext=(3, 3),
                textcoords="offset points",
            )
        axis.set_xlabel("honest-agent false-positive rate $\\alpha$")
        axis.set_ylabel("False credit rate (%)")
        axis.set_title("Unfiltered grading rewards high-FPR detectors")
        axis.grid(alpha=0.3)
        axis.legend(fontsize=7)
        fig.tight_layout()
        fig.savefig(out / "fig_false_credit.png", dpi=180)
        plt.close(fig)

    return {
        "curve": [
            {
                "alpha": r.alpha,
                "p_release": r.p_release,
                "p_delivered": r.p_delivered,
                "false_credit_rate": r.p_false_credit,
                "missed_credit_rate": r.p_missed_credit,
                "inflation_pp": r.inflation_pp,
            }
            for r in curve
        ],
        "monotonicity": monotone,
        "tie_free_bound": {
            "alpha": bound.alpha,
            "beta": bound.beta,
            "p_false_credit": bound.p_false_credit,
            "p_missed_credit": bound.p_missed_credit,
        },
        "archive_ties": {
            "false_credits": len(archive_fc),
            "false_credits_tied_release": int(tied_release),
            "false_credits_unique_release": int(len(archive_fc) - tied_release),
            "missed_credits": len(archive_mc),
            "missed_credits_tied_eligible": int(tied_eligible),
        },
        "profiles": profiles,
        "theorem": theorem_statement(),
    }


# --------------------------------------------------------------------------- #
# Experiment 3: shadow contamination
# --------------------------------------------------------------------------- #
def run_shadow(debates, out: Path, *, figure: bool) -> dict:
    print("\n=== 3. Pre-exclusion epistemic shadow contamination ===")
    summary = shadow_summary(debates)
    rows = []
    for task, cell in summary["by_task"].items():
        rows.append(
            [TASK_LABELS.get(task, task), cell["debates"], cell["contaminated"],
             f"{cell['rate_percent']:.2f}"]
        )
    rows.append(["MIDRULE"])
    for graph, cell in summary["by_graph"].items():
        rows.append([f"topology: {graph}", cell["debates"], cell["contaminated"],
                     f"{cell['rate_percent']:.2f}"])
    print_table(
        "Debates where an honest agent adopted the attack target from a not-yet-flagged insider",
        ["Cell", "Debates", "Contaminated", "Rate %"],
        rows,
    )
    print(
        f"detector debates: {summary['detector_rate_percent']:.2f}% "
        f"({summary['contaminated_debates']} debates, {summary['events']} events); "
        f"disabled controls: {summary['control_rate_percent']:.2f}%"
    )
    print(
        f"delivered failures: {summary['delivered_failures']}; mean events per "
        f"contaminated debate: {summary['mean_events_per_contaminated_debate']:.2f}"
    )
    latex_table(
        out / "Table_Shadow.tex",
        "Pre-exclusion shadow contamination: honest agents that held the gold answer, "
        "read a not-yet-flagged adjacent insider, adopted the attack target, and left the "
        "delivered answer wrong.",
        "tab:shadow",
        ["Cell", "Debates", "Contaminated", "Rate (\\%)"],
        rows,
        note="Conditioned on a delivered failure. GSM8K never adopts the letter target, "
        "so its contamination rate is zero by construction of the attack.",
        col_spec="lrrr",
    )

    if figure:
        fig, axis = plt.subplots(figsize=(6.4, 3.6))
        cells = summary["by_graph"]
        names = list(cells)
        axis.bar(names, [cells[name]["rate_percent"] for name in names], color="#4c72b0")
        axis.set_ylabel("contaminated debates (%)")
        axis.set_title("Shadow contamination by topology")
        axis.grid(axis="y", alpha=0.3)
        fig.tight_layout()
        fig.savefig(out / "fig_shadow.png", dpi=180)
        plt.close(fig)

    return summary


# --------------------------------------------------------------------------- #
# Experiment 4: detector leaderboard
# --------------------------------------------------------------------------- #
def _row_metrics(
    name: str,
    debates: Sequence,
    correct: Mapping[tuple, bool],
    released: Mapping[tuple, bool],
    questions: set[tuple[str, int]],
    slices,
    extras: Mapping[str, set[tuple]] | None = None,
) -> dict:
    keys = [d.key for d in debates if d.question_key in questions]
    delivered = [correct[key] for key in keys]
    released_values = [released[key] for key in keys]
    row = {
        "name": name,
        "debates": len(keys),
        "delivered_percent": mean_percent(delivered),
        "released_percent": mean_percent(released_values),
        "inflation_pp": mean_percent(released_values) - mean_percent(delivered),
        "false_credits": int(sum(r and not c for r, c in zip(released_values, delivered))),
        "missed_credits": int(sum(c and not r for r, c in zip(released_values, delivered))),
        "true_adversarial_percent": mean_percent(
            [correct[d.key] for d in debates
             if d.question_key in questions and in_slice(d, "TRUE_ADVERSARIAL_236", slices)]
        ),
        "self_sabotaged_percent": mean_percent(
            [correct[d.key] for d in debates
             if d.question_key in questions and in_slice(d, "SELF_SABOTAGED_64", slices)]
        ),
        "csqa_tree_percent": mean_percent(
            [correct[d.key] for d in debates
             if d.question_key in questions and d.dataset == "CSQA" and d.graph == "tree"]
        ),
        "mmlu_random_percent": mean_percent(
            [correct[d.key] for d in debates
             if d.question_key in questions and d.dataset == "MMLU" and d.graph == "random"]
        ),
    }
    if extras:
        for label, keyset in extras.items():
            row[label] = mean_percent(
                [correct[k] for k in keys if k in keyset]
            )
    return row


def _oracle_insider(debates: Sequence) -> float:
    values = []
    for debate in debates:
        flags = [1 if i in debate.insiders else 0 for i in range(debate.n_agents)]
        values.append(deliver(debate.votes, flags, debate.gold, debate.dataset).correct)
    return mean_percent(values)


def prepare_guard(debates, *, tune_fraction: float, seed: int) -> dict:
    """Tune both guard modes once and precompute every Task 2 arm."""
    detector_debates = [d for d in debates if not d.is_control]
    controls = [d for d in debates if d.is_control]
    tune_questions, held_questions = split_questions(
        debates, fraction=tune_fraction, seed=seed
    )
    tune = [d for d in detector_debates if d.question_key in tune_questions]
    held = [d for d in detector_debates if d.question_key in held_questions]
    guard = EpistemicGuard()
    tuning = guard.fit(tune)
    hard = guard.predict_hard(detector_debates)
    soft = guard.predict_soft(detector_debates)
    hard_correct = {d.key: bool(hard["correct"][i]) for i, d in enumerate(detector_debates)}
    soft_correct = {d.key: bool(soft["correct"][i]) for i, d in enumerate(detector_debates)}
    released = {
        d.key: releases(d.votes, d.gold, d.dataset)[1] for d in detector_debates
    }
    baseline_correct: dict[str, dict[tuple, bool]] = {}
    baseline_released: dict[str, dict[tuple, bool]] = {}
    for method in DETECTORS:
        subset = [d for d in detector_debates if d.method == method]
        baseline_correct[method] = {d.key: score_debate(d).g_del for d in subset}
        baseline_released[method] = {
            d.key: score_debate(d).g_release for d in subset
        }
    control_correct = {d.key: score_debate(d).g_del for d in controls}
    control_released = {d.key: score_debate(d).g_release for d in controls}

    # -- Task 2: rollback arms and the rehabilitation ensemble ---------- #
    hard_flags = hard["flags"]
    rollback_correct: dict[tuple, bool] = {}
    oracle_rollback_correct: dict[tuple, bool] = {}
    rolled_votes = 0
    oracle_rolled_votes = 0
    for i, debate in enumerate(detector_debates):
        delivery, _, links = rollback_delivery(debate, hard_flags[i])
        rollback_correct[debate.key] = delivery.correct
        rolled_votes += len(links)
        oracle_health, _, oracle_links = rollback_delivery(debate, oracle_flags(debate))
        oracle_rollback_correct[debate.key] = oracle_health.correct
        oracle_rolled_votes += len(oracle_links)
    ensemble_tuning = tune_ensemble(tune, guard)
    ens_data = GuardData(detector_debates, guard.params.gamma)
    ens_p = ens_data.suspicion(guard.params)
    ensemble_correct: dict[tuple, bool] = {}
    ensemble_flags_by_key: dict[tuple, tuple[int, ...]] = {}
    for row, debate in enumerate(detector_debates):
        result = ensemble_result(
            debate,
            ens_p[row],
            debate.flags,
            ensemble_tuning.params,
            stub=ens_data.stub[row],
            bloc=ens_data.bloc[row],
        )
        ensemble_correct[debate.key] = result["delivery"].correct
        ensemble_flags_by_key[debate.key] = tuple(int(f) for f in result["flags"])
    return {
        "seed": seed,
        "debates": list(debates),
        "detector_debates": detector_debates,
        "controls": controls,
        "tune_questions": tune_questions,
        "held_questions": held_questions,
        "tune": tune,
        "held": held,
        "guard": guard,
        "tuning": tuning,
        "hard": hard,
        "soft": soft,
        "hard_correct": hard_correct,
        "soft_correct": soft_correct,
        "released": released,
        "baseline_correct": baseline_correct,
        "baseline_released": baseline_released,
        "control_correct": control_correct,
        "control_released": control_released,
        "rollback_correct": rollback_correct,
        "oracle_rollback_correct": oracle_rollback_correct,
        "rolled_votes": rolled_votes,
        "oracle_rolled_votes": oracle_rolled_votes,
        "ensemble_tuning": ensemble_tuning,
        "ensemble_correct": ensemble_correct,
        "ensemble_flags_by_key": ensemble_flags_by_key,
    }


def run_guard(prepared: dict, out: Path, *, n_boot: int) -> dict:
    print("\n=== 4. EpistemicGuard head-to-head ===")
    debates = prepared["debates"]
    detector_debates = prepared["detector_debates"]
    controls = prepared["controls"]
    tune_questions = prepared["tune_questions"]
    held_questions = prepared["held_questions"]
    tune = prepared["tune"]
    held = prepared["held"]
    tuning = prepared["tuning"]
    hard = prepared["hard"]
    soft = prepared["soft"]
    hard_correct = prepared["hard_correct"]
    soft_correct = prepared["soft_correct"]
    released = prepared["released"]
    baseline_correct = prepared["baseline_correct"]
    baseline_released = prepared["baseline_released"]
    control_correct = prepared["control_correct"]
    control_released = prepared["control_released"]
    rollback_correct = prepared["rollback_correct"]
    oracle_rollback_correct = prepared["oracle_rollback_correct"]
    ensemble_tuning = prepared["ensemble_tuning"]
    ensemble_correct = prepared["ensemble_correct"]
    seed = prepared["seed"]

    slices = slices_of(debates)
    rows_full: list[dict] = []
    rows_held: list[dict] = []
    for method in DETECTORS:
        subset = [d for d in detector_debates if d.method == method]
        rows_full.append(
            _row_metrics(method, subset, baseline_correct[method],
                         baseline_released[method], slices.all_questions, slices)
        )
        rows_held.append(
            _row_metrics(method, subset, baseline_correct[method],
                         baseline_released[method], held_questions, slices)
        )
    extra_arms = {
        GUARD_ROLLBACK: rollback_correct,
        ORACLE_ROLLBACK: oracle_rollback_correct,
        GUARD_ENSEMBLE: ensemble_correct,
    }
    for name, correct in (
        (GUARD_HARD, hard_correct),
        (GUARD_SOFT, soft_correct),
        *extra_arms.items(),
    ):
        rows_full.append(
            _row_metrics(name, detector_debates, correct, released,
                         slices.all_questions, slices)
        )
        rows_held.append(
            _row_metrics(name, detector_debates, correct, released,
                         held_questions, slices)
        )
    rows_full.append(
        _row_metrics(NO_DETECTOR, controls, control_correct, control_released,
                     slices.all_questions, slices)
    )
    rows_held.append(
        _row_metrics(NO_DETECTOR, controls, control_correct, control_released,
                     held_questions, slices)
    )

    full_by_name = {row["name"]: row for row in rows_full}
    held_by_name = {row["name"]: row for row in rows_held}
    print("\nHeld-out delivered accuracy (80% of question IDs, tuned on 20%):")
    print_table(
        "Leaderboard",
        ["Detector", "n", "g_del %", "g_rel %", "FC", "TrueAdv %", "SelfSab %", "CSQA+Tree %"],
        [
            [
                name,
                held_by_name[name]["debates"],
                f"{held_by_name[name]['delivered_percent']:.2f}",
                f"{held_by_name[name]['released_percent']:.2f}",
                held_by_name[name]["false_credits"],
                f"{held_by_name[name]['true_adversarial_percent']:.2f}",
                f"{held_by_name[name]['self_sabotaged_percent']:.2f}",
                f"{held_by_name[name]['csqa_tree_percent']:.2f}",
            ]
            for name in LEADERBOARD
        ],
    )

    readable = [
        "Detector", "n", "$g_{del}$ (held)", "$g_{del}$ (full)", "$g_{rel}$ (full)",
        "FC", "MC", "TrueAdv", "SelfSab", "CSQA+Tree", "MMLU+Random",
    ]
    latex_rows = []
    for name in LEADERBOARD:
        held_row = held_by_name[name]
        full_row = full_by_name.get(name, held_row)
        latex_rows.append(
            [
                name,
                held_row["debates"],
                f"{held_row['delivered_percent']:.2f}",
                f"{full_row['delivered_percent']:.2f}",
                f"{full_row['released_percent']:.2f}",
                full_row["false_credits"],
                full_row["missed_credits"],
                f"{full_row['true_adversarial_percent']:.2f}",
                f"{full_row['self_sabotaged_percent']:.2f}",
                f"{full_row['csqa_tree_percent']:.2f}",
                f"{full_row['mmlu_random_percent']:.2f}",
            ]
        )
    latex_table(
        out / "Table_Leaderboard.tex",
        "Head-to-head delivered accuracy. Hyperparameters for both EpistemicGuard modes "
        "were tuned on 20\\% of question IDs per task; the held-out column is the remaining "
        "80\\%, the full column restores all 400 questions for comparability with the audit.",
        "tab:leaderboard",
        readable,
        latex_rows,
        note="Baselines are evaluated on their own 1,600 detector debates; EpistemicGuard "
        "is pooled over all 9,600 detector debates (six baseline conversation sets). "
        "The no-detector row is the disabled control.",
        col_spec="lrrrrrrrrrr",
    )

    # -- 16 task x topology cells ---------------------------------------- #
    def cell_table(
        correct: Mapping[tuple, bool],
        debates: Sequence,
        questions: set[tuple[str, int]],
    ) -> dict[str, float]:
        table: dict[str, float] = {}
        for task in TASKS:
            for graph in TOPOLOGIES:
                keys = [
                    d.key for d in debates
                    if d.question_key in questions
                    and d.dataset == task and d.graph == graph
                ]
                table[f"{TASK_LABELS[task]} + {graph}"] = mean_percent(
                    [correct[key] for key in keys]
                )
        return table

    cells: dict[str, dict[str, float]] = {}
    for method in DETECTORS:
        subset = [d for d in detector_debates if d.method == method]
        cells[method] = cell_table(baseline_correct[method], subset, held_questions)
    cells[GUARD_HARD] = cell_table(hard_correct, detector_debates, held_questions)
    cells[GUARD_SOFT] = cell_table(soft_correct, detector_debates, held_questions)
    cell_names = list(cells[DETECTORS[0]])
    cell_rows = [
        [name]
        + [f"{cells[column][name]:.1f}" for column in [*DETECTORS, GUARD_HARD, GUARD_SOFT]]
        for name in cell_names
    ]
    latex_table(
        out / "Table_Cells.tex",
        "Held-out delivered accuracy on the 16 task $\\times$ topology cells. The CSQA + tree "
        "and MMLU + random cells are where the released ranking inverts most sharply.",
        "tab:cells",
        ["Cell", *DETECTORS, GUARD_HARD, GUARD_SOFT],
        cell_rows,
        note="Cell values are percentages over the 320 held-out question IDs per task.",
        col_spec="lrrrrrrrr",
    )

    # -- paired inference, within each baseline's own conversation set --- #
    # A pooled comparison would pair a baseline's 1,280 debates against the
    # guard's 7,680, mixing six different conversation sets. The valid paired
    # test compares the guard with a baseline on that baseline's own debates.
    held_detector = [d for d in detector_debates if d.question_key in held_questions]
    stats_rows = []
    stats_payload: dict[str, dict] = {}
    within: dict[str, dict[str, float]] = {GUARD_HARD: {}, GUARD_SOFT: {}}
    for guard_name, guard_correct in (
        (GUARD_HARD, hard_correct),
        (GUARD_SOFT, soft_correct),
    ):
        p_values = {}
        for method in DETECTORS:
            subset = [d for d in held_detector if d.method == method]
            guard_subset = {d.key: bool(guard_correct[d.key]) for d in subset}
            base_scores = question_scores(subset, baseline_correct[method])
            guard_scores = question_scores(subset, guard_subset)
            boot, (statistic, p) = paired_comparison(
                base_scores, guard_scores, n_boot=n_boot, seed=seed
            )
            label = f"{guard_name} vs {method}"
            p_values[label] = (statistic, p)
            within[guard_name][method] = boot["mean_pp"]
            stats_payload[label] = {
                "comparison_set": method,
                "delta_pp": boot["mean_pp"],
                "ci_low_pp": boot["ci_low_pp"],
                "ci_high_pp": boot["ci_high_pp"],
                "p_value": p,
                "per_task": boot["per_task"],
            }
        adjusted = holm_table(p_values)
        for label, cell in adjusted.items():
            payload = stats_payload[label]
            payload["p_holm"] = cell["p_holm"]
            stats_rows.append(
                [
                    f"{label} ({payload['comparison_set']} debates)",
                    f"{payload['delta_pp']:+.2f}",
                    f"[{payload['ci_low_pp']:+.2f}, {payload['ci_high_pp']:+.2f}]",
                    f"{payload['p_value']:.4f}",
                    f"{payload['p_holm']:.4f}",
                    "*" if payload["p_holm"] < 0.05 else "",
                ]
            )
    print_table(
        "Paired within-conversation bootstrap (10k) and Wilcoxon, Holm-corrected",
        ["Comparison", "Delta pp", "95% CI", "p", "p_Holm", ""],
        stats_rows,
    )
    latex_table(
        out / "Table_Stats.tex",
        "Held-out paired comparisons of EpistemicGuard against each baseline on that "
        "baseline's own debate set. Intervals resample question IDs within task and "
        "average tasks equally; Wilcoxon signed-rank tests are Holm-corrected per mode.",
        "tab:stats",
        ["Comparison", "$\\Delta$ (pp)", "95\\% CI", "$p$", "$p_{Holm}$", ""],
        stats_rows,
        note="Positive $\\Delta$ means EpistemicGuard is more accurate than the baseline on "
        "the same debates and the same terminal votes.",
        col_spec="lrrrrl",
    )

    # -- Task 2 leaderboard: rollback and rehabilitation ------------------ #
    def held_stratum_delta(correct: Mapping[tuple, bool]) -> float:
        values = []
        for method in DETECTORS:
            subset = [
                d for d in detector_debates
                if d.method == method and d.question_key in held_questions
            ]
            if not subset:
                continue
            arm = mean_percent([correct[d.key] for d in subset])
            base = mean_percent([baseline_correct[method][d.key] for d in subset])
            values.append(arm - base)
        return float(np.mean(values)) if values else 0.0

    ensemble_rehab = 0
    ensemble_missed = 0
    for debate in detector_debates:
        ens = prepared["ensemble_flags_by_key"][debate.key]
        for j in range(debate.n_agents):
            if debate.flags[j] and not ens[j]:
                ensemble_rehab += 1
            elif not debate.flags[j] and ens[j]:
                ensemble_missed += 1
    rollback_rows = []
    for name, correct, interventions in (
        (GUARD_ROLLBACK, rollback_correct, prepared["rolled_votes"]),
        (ORACLE_ROLLBACK, oracle_rollback_correct, prepared["oracle_rolled_votes"]),
        (GUARD_ENSEMBLE, ensemble_correct, ensemble_rehab),
    ):
        rollback_rows.append(
            [
                name,
                f"{full_by_name[name]['delivered_percent']:.2f}",
                f"{held_by_name[name]['delivered_percent']:.2f}",
                interventions,
                f"{held_stratum_delta(correct):+.2f}",
            ]
        )
    print_table(
        "Epistemic rollback and rehabilitation (held-out, delta vs each baseline "
        "on its own debates)",
        ["Arm", "g_del full", "g_del held", "Interventions", "Delta pp"],
        rollback_rows,
    )
    print(
        f"ensemble thresholds: {ensemble_tuning.params.as_dict()}; tuned on "
        f"{ensemble_tuning.split_size} debates ({ensemble_tuning.evaluated} configs), "
        f"rehabilitated {ensemble_rehab} flags, flagged {ensemble_missed} missed agents"
    )
    latex_table(
        out / "Table_Rollback.tex",
        "Epistemic rollback and the rehabilitation ensemble. Rollback restores the "
        "pre-contact belief of an honest voter that copied a flagged neighbour; the "
        "ensemble first unflags benign agents, then flags missed insiders, then rolls back.",
        "tab:rollback",
        ["Arm", "$g_{del}$ (full)", "$g_{del}$ (held)", "Interventions", "$\\Delta$ (pp)"],
        rollback_rows,
        note="Interventions are rolled-back votes (rollback arms) or rehabilitated flags "
        "(ensemble). The ensemble also flagged "
        f"{ensemble_missed} previously unflagged agents. $\\Delta$ averages the held-out "
        "within-stratum delta against each baseline on that baseline's own debates.",
        col_spec="lrrrr",
    )

    # -- supplementary diagnostics --------------------------------------- #
    oracle_held = _oracle_insider(held_detector)
    guard_hard_held = held_by_name[GUARD_HARD]["delivered_percent"]
    best_baseline = max(
        ((held_by_name[m]["delivered_percent"], m) for m in DETECTORS)
    )
    strata = {}
    for method in DETECTORS:
        idx = [i for i, d in enumerate(detector_debates) if d.method == method]
        strata[method] = {
            "debates": len(idx),
            "baseline_percent": full_by_name[method]["delivered_percent"],
            "hard_percent": mean_percent([hard["correct"][i] for i in idx]),
            "soft_percent": mean_percent([soft["correct"][i] for i in idx]),
        }
    hard_within = within[GUARD_HARD]
    soft_within = within[GUARD_SOFT]
    significant = {
        mode: [
            method for method in DETECTORS
            if stats_payload[f"{mode} vs {method}"].get("p_holm", 1.0) < 0.05
            and stats_payload[f"{mode} vs {method}"]["delta_pp"] > 0
        ]
        for mode in (GUARD_HARD, GUARD_SOFT)
    }
    weakly_dominates = all(hard_within[m] >= -1e-9 for m in DETECTORS)
    strict_all = all(
        hard_within[m] > 0
        and stats_payload[f"{GUARD_HARD} vs {m}"].get("p_holm", 1.0) < 0.05
        for m in DETECTORS
    )
    print(
        f"\nPooled held-out: hard {guard_hard_held:.2f}%, soft "
        f"{held_by_name[GUARD_SOFT]['delivered_percent']:.2f}%; best pooled baseline "
        f"{best_baseline[1]} {best_baseline[0]:.2f}%. Pooled comparisons are unpaired "
        "(different conversation sets) and are reported only for context."
    )
    print(
        "Within each baseline's own debates, Guard-Hard delta (pp): "
        + "; ".join(f"{m} {hard_within[m]:+.2f}" for m in DETECTORS)
    )
    print(
        f"weakly dominates all six: {weakly_dominates}; significant improvements: "
        f"{significant[GUARD_HARD]}; oracle (true insiders excluded) {oracle_held:.2f}%."
    )
    if not strict_all:
        print(
            "VERDICT: a strict 'outperforms all six' claim is NOT supported. The guard "
            "matches or exceeds every baseline on its own debates, but ties XG-Guard "
            "and has non-significant gains over CASPIAN and TAM. The pooled oracle gap "
            "is decomposed in Table_OracleParadox: it is mostly a composition effect, "
            "not a set of debates the oracle loses to XG-Guard."
        )

    if True:
        fig, axis = plt.subplots(figsize=(6.8, 4.0))
        names = LEADERBOARD
        values = [held_by_name[name]["delivered_percent"] for name in names]
        colors = (
            ["#8c8c8c"] * len(DETECTORS)
            + ["#c44e52", "#4c72b0"]
            + ["#55a868", "#8172b3", "#937860", "#dd8452"]
        )
        axis.barh(names, values, color=colors)
        axis.axvline(values[names.index(NO_DETECTOR)], color="black", linewidth=0.8, linestyle=":")
        axis.set_xlabel("held-out delivered accuracy (%)")
        axis.set_xlim(min(values) - 3, 100)
        axis.set_title("Delivered accuracy, 80% held-out questions")
        for position, value in enumerate(values):
            axis.text(value + 0.3, position, f"{value:.2f}", va="center", fontsize=7)
        axis.grid(axis="x", alpha=0.3)
        fig.tight_layout()
        fig.savefig(out / "fig_leaderboard.png", dpi=180)
        plt.close(fig)

    return {
        "tuning": {
            "params": tuning.params.as_dict(),
            "tune_accuracy_percent": tuning.tune_accuracy_percent,
            "tune_accuracy_soft_percent": tuning.tune_accuracy_soft_percent,
            "evaluated": tuning.evaluated,
            "tune_questions": len(tune_questions),
            "held_questions": len(held_questions),
            "tune_debates": len(tune),
            "held_debates": len(held),
        },
        "full": rows_full,
        "held_out": rows_held,
        "strata": strata,
        "oracle_insider_held_out_percent": oracle_held,
        "rollback": {
            "ensemble_params": ensemble_tuning.params.as_dict(),
            "ensemble_tune_accuracy_percent": ensemble_tuning.tune_accuracy_percent,
            "ensemble_tune_by_method": ensemble_tuning.by_method,
            "ensemble_configs_evaluated": ensemble_tuning.evaluated,
            "ensemble_rehabilitated_flags": ensemble_rehab,
            "ensemble_missed_flags": ensemble_missed,
            "rolled_votes_guard": prepared["rolled_votes"],
            "rolled_votes_oracle": prepared["oracle_rolled_votes"],
            "held_delta_pp": {
                name: held_stratum_delta(correct)
                for name, correct in (
                    (GUARD_ROLLBACK, rollback_correct),
                    (ORACLE_ROLLBACK, oracle_rollback_correct),
                    (GUARD_ENSEMBLE, ensemble_correct),
                )
            },
        },
        "guard_hard_mean_flags": hard["mean_flags"],
        "guard_soft_mean_suspicion": float(hard["p"].mean()),
        "empty_eligible": hard["empty_eligible"],
        "stats": stats_payload,
        "within_stratum_delta_pp": within,
        "cells_16": cells,
        "verdict": {
            "beats_all_six_strictly": bool(strict_all),
            "weakly_dominates_within_strata": bool(weakly_dominates),
            "significant_improvements_hard": significant[GUARD_HARD],
            "significant_improvements_soft": significant[GUARD_SOFT],
            "best_pooled_baseline": best_baseline[1],
            "best_pooled_baseline_percent": best_baseline[0],
            "guard_hard_pooled_percent": guard_hard_held,
            "guard_soft_pooled_percent": held_by_name[GUARD_SOFT]["delivered_percent"],
            "oracle_insider_percent": oracle_held,
        },
    }


# --------------------------------------------------------------------------- #
# Experiment 1b: the Oracle Paradox
# --------------------------------------------------------------------------- #
def run_oracle(debates, out: Path, prepared: dict, *, figure: bool) -> dict:
    print("\n=== 1b. Oracle Paradox decomposition ===")
    extra = {
        GUARD_HARD: {
            d.key: [int(flag) for flag in prepared["hard"]["flags"][i]]
            for i, d in enumerate(prepared["detector_debates"])
        },
        GUARD_ENSEMBLE: prepared["ensemble_flags_by_key"],
    }
    payload = decompose_oracle_paradox(debates, extra_arms=extra)
    arms = ["Unfiltered", "Oracle", *DETECTORS, GUARD_HARD, GUARD_ENSEMBLE]
    rows = []
    for arm in arms:
        rows.append(
            [arm]
            + [
                f"{payload['by_slice'][name][arm]['g_del_percent']:.2f}"
                for name in ORACLE_SLICES
            ]
        )
    print_table(
        "Delivered accuracy by attack-validity slice (Oracle vs detectors)",
        ["Arm", "Self-sabotaged 64", "True adversarial 236", "GSM8K 100", "All"],
        rows,
    )
    latex_table(
        out / "Table_OracleParadox.tex",
        "Oracle accuracy by attack-validity slice. The oracle trails XG-Guard only on "
        "true-adversarial questions (81.67 vs 83.58) and leads it on self-sabotaged "
        "ones (86.52 vs 85.55), where excluding the gold-voting insiders costs it "
        "accuracy; the pooled deficit is compositional.",
        "tab:oracle-paradox",
        ["Arm", "Self-sab. 64", "True adv. 236", "GSM8K 100", "All"],
        rows,
        note="$g_{del}$ percentages. Baseline rows cover that baseline's own 1,600 "
        "debates (256 / 944 / 400 per slice); the oracle, unfiltered tally and guard "
        "arms are pooled over all 9,600, so only the within-set panel is a paired "
        "comparison. The unfiltered row is the released tally, not a defense.",
        col_spec="lrrrr",
    )

    within_rows = []
    for method, cell in payload["within_stratum"].items():
        discord = payload["discordance"][method]
        within_rows.append(
            [
                method,
                cell["debates"],
                f"{cell['oracle_percent']:.2f}",
                f"{cell['detector_percent']:.2f}",
                f"{cell['delta_pp']:+.2f}",
                discord["detector_only"],
                discord["oracle_only"],
            ]
        )
    print_table(
        "Oracle vs each detector on that detector's own 1,600 debates",
        ["Conversation set", "n", "Oracle %", "Detector %", "Delta pp", "Det-only", "Oracle-only"],
        within_rows,
    )
    types = payload["discordance_types"]
    print(
        f"discordance types where a detector succeeds and the oracle fails: "
        f"Type I {types['I']}, Type II {types['II']}, Type III {types['III']}, other {types['other']}"
    )
    print(
        f"XG-Guard vs oracle 2x2: both {payload['xg_oracle_table']['both']}, "
        f"XG-only {payload['xg_oracle_table']['xg_only']}, "
        f"oracle-only {payload['xg_oracle_table']['oracle_only']}, "
        f"neither {payload['xg_oracle_table']['neither']}"
    )
    print(payload["verdict"])
    latex_table(
        out / "Table_OracleWithin.tex",
        "Within-conversation-set comparison of the true-insider oracle and each detector. "
        "The oracle beats every baseline on that baseline's own debates except XG-Guard, "
        "where it trails by 0.06 pp; the pooled oracle gap is therefore a composition effect.",
        "tab:oracle-within",
        ["Conversation set", "n", "Oracle (\\%)", "Detector (\\%)", "$\\Delta$ (pp)",
         "Det.-only", "Oracle-only"],
        within_rows,
        note="Detector-only counts debates where the detector is delivered-correct and the "
        "oracle is wrong; of these, Type I/II/III counts are "
        f"{types['I']}/{types['II']}/{types['III']} (other {types['other']}). "
        f"On XG-Guard's own debates the two disagree in only "
        f"{payload['xg_oracle_table']['xg_only'] + payload['xg_oracle_table']['oracle_only']} "
        "debates.",
        col_spec="lrrrrrr",
    )

    if figure:
        slices = ["SELF_SABOTAGED_64", "TRUE_ADVERSARIAL_236", "GSM8K_100"]
        labels = ["self-sab. 64", "true adv. 236", "GSM8K 100"]
        fig, (left, right) = plt.subplots(1, 2, figsize=(9.2, 3.8))
        width = 0.26
        positions = np.arange(len(slices))
        for offset, (arm, color) in enumerate(
            (("Unfiltered", "#999999"), ("Oracle", "#4c72b0"), ("XG-Guard", "#c44e52"))
        ):
            values = [payload["by_slice"][name][arm]["g_del_percent"] for name in slices]
            left.bar(positions + (offset - 1) * width, values, width, label=arm, color=color)
        left.set_xticks(positions, labels)
        left.set_ylabel("delivered accuracy (%)")
        left.set_ylim(70, 100)
        left.set_title("Oracle vs detectors by slice")
        left.legend(fontsize=7)
        left.grid(axis="y", alpha=0.3)

        methods = list(payload["within_stratum"])
        deltas = [payload["within_stratum"][m]["delta_pp"] for m in methods]
        colors = ["#c44e52" if value < 0 else "#55a868" for value in deltas]
        right.barh(methods, deltas, color=colors)
        right.axvline(0.0, color="black", linewidth=0.8)
        for y, value in enumerate(deltas):
            offset = -0.08 if value < 0 else 0.08
            right.text(value + offset, y, f"{value:+.2f}", va="center",
                       ha="right" if value < 0 else "left", fontsize=7)
        right.set_xlim(min(deltas) - 0.9, max(deltas) + 0.9)
        right.set_xlabel("oracle minus detector (pp), same debates")
        right.set_title("Within-set: oracle is not the loser")
        right.grid(axis="x", alpha=0.3)
        fig.tight_layout()
        fig.savefig(out / "fig_oracle_paradox.png", dpi=180)
        plt.close(fig)

    return payload


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #
def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--handoff", type=Path, default=None)
    parser.add_argument("--out", type=Path, default=ROOT / "artifacts")
    parser.add_argument(
        "--only",
        choices=("clean", "theory", "shadow", "oracle", "guard", "all"),
        default="all",
    )
    parser.add_argument("--bootstrap", type=int, default=10_000)
    parser.add_argument("--seed", type=int, default=20261112)
    parser.add_argument("--tune-fraction", type=float, default=0.2)
    parser.add_argument("--fast", action="store_true", help="fewer MC draws and resamples")
    parser.add_argument("--no-figures", action="store_true")
    args = parser.parse_args(argv)

    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    n_sim = 30_000 if args.fast else 120_000
    n_boot = 2_000 if args.fast else args.bootstrap
    figures = not args.no_figures

    debates = load_debates(args.handoff)
    (out / "schema.txt").write_text(schema_report(args.handoff) + "\n", encoding="utf-8")
    print(f"loaded {len(debates)} debates from {Path(args.handoff).resolve() if args.handoff else 'auto-discovery'}")
    print(
        f"detector debates: {sum(1 for d in debates if not d.is_control)}; "
        f"controls: {sum(1 for d in debates if d.is_control)}; "
        f"questions: {len({d.question_key for d in debates})}"
    )
    print(
        "trajectories: "
        f"{sum(1 for d in debates if d.has_trajectory)} debates with a raw round grid; "
        f"rounds per debate: {sorted({len(d.rounds) for d in debates})}"
    )

    results: dict = {
        "meta": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "commit": "53be3249ebfa631d8e960c9fb1c931d526654697",
            "debates": len(debates),
            "detector_debates": sum(1 for d in debates if not d.is_control),
            "control_debates": sum(1 for d in debates if d.is_control),
            "questions": len({d.question_key for d in debates}),
            "seed": args.seed,
            "reference": REFERENCE,
        }
    }
    if args.only in ("clean", "all"):
        results["clean"] = run_clean(debates, out)
    if args.only in ("theory", "all"):
        results["theory"] = run_theory(debates, out, n_sim=n_sim, figure=figures)
    if args.only in ("shadow", "all"):
        results["shadow"] = run_shadow(debates, out, figure=figures)
    prepared = None
    if args.only in ("oracle", "guard", "all"):
        prepared = prepare_guard(
            debates, tune_fraction=args.tune_fraction, seed=args.seed
        )
    if args.only in ("oracle", "all"):
        results["oracle_paradox"] = run_oracle(
            debates, out, prepared, figure=figures
        )
    if args.only in ("guard", "all"):
        results["guard"] = run_guard(prepared, out, n_boot=n_boot)

    write_json(out / "results.json", results)
    print(f"\nartifacts written to {out.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
