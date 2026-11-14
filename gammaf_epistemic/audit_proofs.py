"""Systematic-failure proofs for the unfiltered GAMMAF evaluator.

Two analyses:

``false_credit``
    A 7-honest / 3-insider debate model with a detector of false-positive rate
    ``alpha`` and true-positive rate ``1 - beta``.  The released score grades all
    ten votes; the delivered score grades only the unflagged ones.  Because the
    honest votes a high-FPR detector expels are disproportionately *correct*, the
    unfiltered tally keeps their support while the delivered tally loses it:
    false credit rises with ``alpha``.

``shadow_audit``
    Pre-exclusion contamination: an insider's messages are read by honest
    neighbours for rounds *before* it is flagged, so a flagged insider can still
    have caused the delivered failure it is credited with preventing.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, Sequence

import numpy as np

from .data import (
    CONTROL,
    DETECTORS,
    N_AGENTS,
    N_INSIDERS,
    TASKS,
    TOPOLOGIES,
    Debate,
)
from .gammaf_clean import check, deliver, plurality, score_debate

# --------------------------------------------------------------------------- #
# False-credit model
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class CreditRates:
    """Population rates under the analytic debate model."""

    alpha: float
    beta: float
    p_release: float
    p_delivered: float
    p_false_credit: float
    p_missed_credit: float

    @property
    def inflation_pp(self) -> float:
        return 100.0 * (self.p_release - self.p_delivered)


def _plurality_ids(votes: np.ndarray, keep: np.ndarray) -> np.ndarray:
    """First-occurrence plurality over a masked (n, k) integer vote matrix."""
    n, k = votes.shape
    categories = int(votes.max()) + 1
    counts = np.zeros((n, categories), dtype=np.int64)
    first = np.full((n, categories), k, dtype=np.int64)
    positions = np.arange(k)[None, :]
    for category in range(categories):
        hit = (votes == category) & keep
        counts[:, category] = hit.sum(axis=1)
        first[:, category] = np.where(hit, positions, k).min(axis=1)
    order = np.lexsort((first, -counts), axis=1)
    return order[:, 0]


def simulate_false_credit(
    p_h: float,
    alpha: float,
    beta: float,
    *,
    n: int = 200_000,
    n_honest: int = 7,
    n_insiders: int = 3,
    n_options: int = 4,
    seed: int = 20261112,
) -> CreditRates:
    """Monte Carlo evaluation of the released vs delivered score.

    Honest agents vote the gold answer with probability ``p_h`` and otherwise a
    uniformly random wrong option; insiders always vote the fixed wrong target
    ``z``.  Honest agents are flagged with probability ``alpha``, insiders with
    probability ``1 - beta``.  Tie-breaking matches ``Counter.most_common``
    (first occurrence in agent order).
    """
    rng = np.random.default_rng(seed)
    wrong = (1.0 - p_h) / max(n_options - 1, 1)
    probs = np.array([p_h] + [wrong] * (n_options - 1), dtype=float)
    probs /= probs.sum()
    honest = rng.choice(n_options, size=(n, n_honest), p=probs)
    votes = np.empty((n, n_honest + n_insiders), dtype=np.int64)
    votes[:, :n_honest] = honest
    votes[:, n_honest:] = 1
    flags = np.zeros((n, n_honest + n_insiders), dtype=bool)
    flags[:, :n_honest] = rng.random((n, n_honest)) < alpha
    flags[:, n_honest:] = rng.random((n, n_insiders)) < (1.0 - beta)
    keep_all = np.ones_like(flags)
    eligible = ~flags
    release = _plurality_ids(votes, keep_all) == 0
    no_eligible = eligible.sum(axis=1) == 0
    delivered = _plurality_ids(votes, eligible) == 0
    delivered &= ~no_eligible
    false_credit = release & ~delivered
    missed_credit = delivered & ~release
    return CreditRates(
        alpha=float(alpha),
        beta=float(beta),
        p_release=float(release.mean()),
        p_delivered=float(delivered.mean()),
        p_false_credit=float(false_credit.mean()),
        p_missed_credit=float(missed_credit.mean()),
    )


def false_credit_curve(
    p_h: float,
    beta: float,
    alphas: Sequence[float],
    *,
    n: int = 100_000,
    n_options: int = 4,
    seed: int = 20261112,
) -> list[CreditRates]:
    return [
        simulate_false_credit(
            p_h, float(a), beta, n=n, n_options=n_options, seed=seed + i
        )
        for i, a in enumerate(alphas)
    ]


def _multinomial(counts: Sequence[int], probs: Sequence[float]) -> float:
    total = sum(counts)
    coefficient = math.factorial(total)
    for count in counts:
        coefficient //= math.factorial(count)
    weight = float(coefficient)
    for count, prob in zip(counts, probs):
        weight *= prob**count
    return weight


def tie_free_credit(
    p_h: float,
    alpha: float,
    beta: float,
    *,
    n_honest: int = 7,
    n_insiders: int = 3,
) -> CreditRates:
    """Exact enumeration under a unique-winner (tie-free) plurality rule.

    This is the tie-free counterpart of :func:`simulate_false_credit`.  It is a
    *lower bound* on the evaluator's false credit, not an approximation of it:
    the released evaluator breaks ties by first occurrence, and that tie rule is
    where most false credit is created.  Use it to separate the two mechanisms
    (expelled correct votes vs. a changed tie winner).
    """
    q = (1.0 - p_h) / 3.0
    probs = (p_h, q, q, q)
    p_release = p_delivered = p_fc = p_mc = 0.0
    for a in range(n_honest + 1):
        for b in range(n_honest - a + 1):
            for c in range(n_honest - a - b + 1):
                d = n_honest - a - b - c
                comp = _multinomial((a, b, c, d), probs)
                if comp == 0.0:
                    continue
                release = int(a > max(b + n_insiders, c, d))
                flag_mass = 0.0
                delivered_mass = 0.0
                for fa in range(a + 1):
                    wa = (
                        math.comb(a, fa)
                        * alpha**fa
                        * (1 - alpha) ** (a - fa)
                    )
                    for fb in range(b + 1):
                        wb = wa * math.comb(b, fb) * alpha**fb * (1 - alpha) ** (b - fb)
                        for fc in range(c + 1):
                            wc = (
                                wb
                                * math.comb(c, fc)
                                * alpha**fc
                                * (1 - alpha) ** (c - fc)
                            )
                            for fd in range(d + 1):
                                w = (
                                    wc
                                    * math.comb(d, fd)
                                    * alpha**fd
                                    * (1 - alpha) ** (d - fd)
                                )
                                for flagged_insiders in range(n_insiders + 1):
                                    wi = (
                                        w
                                        * math.comb(n_insiders, flagged_insiders)
                                        * (1 - beta) ** flagged_insiders
                                        * beta ** (n_insiders - flagged_insiders)
                                    )
                                    if wi == 0.0:
                                        continue
                                    flag_mass += wi
                                    eligible = (a - fa) + (b - fb) + (c - fc) + (d - fd)
                                    eligible += n_insiders - flagged_insiders
                                    if eligible == 0:
                                        continue
                                    z_eligible = (
                                        b - fb + n_insiders - flagged_insiders
                                    )
                                    delivered = int(
                                        (a - fa) > max(z_eligible, c - fc, d - fd)
                                    )
                                    delivered_mass += wi * delivered
                p_release += comp * release
                p_delivered += comp * delivered_mass
                p_fc += comp * (release - delivered_mass)
                p_mc += comp * (delivered_mass - release)
    return CreditRates(
        alpha=float(alpha),
        beta=float(beta),
        p_release=float(p_release),
        p_delivered=float(p_delivered),
        p_false_credit=float(max(p_fc, 0.0)),
        p_missed_credit=float(max(p_mc, 0.0)),
    )


def monotonicity_check(
    p_h: float,
    beta: float,
    alphas: Sequence[float],
    *,
    n: int = 60_000,
    seed: int = 20261112,
) -> dict:
    """Numerical check of the proposition that false credit rises with alpha."""
    rates = false_credit_curve(p_h, beta, alphas, n=n, seed=seed)
    values = [r.p_false_credit for r in rates]
    violations = [
        (alphas[i], alphas[i + 1], values[i], values[i + 1])
        for i in range(len(values) - 1)
        if values[i + 1] < values[i] - 1e-9
    ]
    return {
        "p_h": p_h,
        "beta": beta,
        "alphas": list(alphas),
        "false_credit_rates": values,
        "inflation_pp": [r.inflation_pp for r in rates],
        "violations": violations,
        "nondecreasing": not violations,
    }


def theorem_statement() -> dict:
    """The proposition, its assumptions and the empirical consequence."""
    return {
        "proposition": (
            "Fix the honest accuracy p_h, the insider count K, and the insider "
            "detection rate 1-beta. If honest agents are flagged independently "
            "with false-positive rate alpha, then P(g_release=1, g_del=0) is "
            "nondecreasing in alpha, and strictly increasing whenever the "
            "expected number of excluded correct honest votes crosses a "
            "plurality margin."
        ),
        "assumptions": [
            "Honest votes are exchangeable and correct with probability p_h.",
            "Insider votes are pinned to a non-gold target z.",
            "Flags are independent of the vote draw given agent type.",
            "Released correctness uses the all-agent plurality; delivered "
            "correctness uses the unflagged plurality.",
        ],
        "mechanism": (
            "The released tally counts correct honest votes that the delivered "
            "tally has expelled. Excluding a correct vote can only leave the "
            "eligible plurality weakly worse, while the released plurality is "
            "unchanged, so the disagreement set grows with the number of "
            "expelled correct votes."
        ),
        "corollary": (
            "A detector with alpha=0 can never earn false credit: no honest vote "
            "is expelled, so the two electorates coincide and g_release=g_del."
        ),
    }


# --------------------------------------------------------------------------- #
# Empirical calibration on the archive
# --------------------------------------------------------------------------- #
def detector_profiles(
    debates: Sequence[Debate],
    *,
    methods: Sequence[str] = DETECTORS,
    n_sim: int = 120_000,
    seed: int = 20261112,
) -> dict:
    """Measure each detector's FPR/TPR and compare observed to predicted credit."""
    controls = [d for d in debates if d.is_control]
    honest_votes = 0
    honest_correct = 0
    for debate in controls:
        honest = [i for i in range(debate.n_agents) if i not in debate.insiders]
        for i in honest:
            honest_votes += 1
            honest_correct += int(check(debate.votes[i], debate.gold, debate.dataset))
    p_h = honest_correct / max(honest_votes, 1)

    rows: dict[str, dict] = {}
    for method in methods:
        subset = [d for d in debates if d.method == method]
        honest_flags = 0
        honest_slots = 0
        insider_flags = 0
        insider_slots = 0
        false_credit = 0
        missed_credit = 0
        released = 0
        delivered = 0
        for debate in subset:
            scored = score_debate(debate)
            false_credit += int(scored.false_credit)
            missed_credit += int(scored.missed_credit)
            released += int(scored.g_release)
            delivered += int(scored.g_del)
            insiders = set(debate.insiders)
            for i, flag in enumerate(debate.flags):
                if i in insiders:
                    insider_slots += 1
                    insider_flags += int(flag)
                else:
                    honest_slots += 1
                    honest_flags += int(flag)
        alpha = honest_flags / max(honest_slots, 1)
        tpr = insider_flags / max(insider_slots, 1)
        predicted = simulate_false_credit(
            p_h, alpha, 1.0 - tpr, n=n_sim, seed=seed, n_options=4
        )
        rows[method] = {
            "debates": len(subset),
            "alpha": alpha,
            "tpr": tpr,
            "released_accuracy_percent": 100.0 * released / len(subset),
            "delivered_accuracy_percent": 100.0 * delivered / len(subset),
            "inflation_pp": 100.0 * (released - delivered) / len(subset),
            "false_credits": false_credit,
            "missed_credits": missed_credit,
            "observed_false_credit_rate": false_credit / len(subset),
            "predicted_false_credit_rate": predicted.p_false_credit,
            "predicted_inflation_pp": predicted.inflation_pp,
        }

    observed = np.array([r["observed_false_credit_rate"] for r in rows.values()])
    predicted = np.array([r["predicted_false_credit_rate"] for r in rows.values()])
    alphas = np.array([r["alpha"] for r in rows.values()])
    return {
        "honest_accuracy_under_attack": p_h,
        "rows": rows,
        "correlation_alpha_vs_observed_fc": float(np.corrcoef(alphas, observed)[0, 1]),
        "correlation_predicted_vs_observed": float(np.corrcoef(predicted, observed)[0, 1]),
        "mean_absolute_error": float(np.abs(predicted - observed).mean()),
    }


# --------------------------------------------------------------------------- #
# Pre-exclusion epistemic shadow contamination
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class ShadowEvent:
    debate: tuple[str, str, int, str]
    honest_agent: int
    insider: int
    round_position: int

    def as_dict(self) -> dict:
        dataset, method, item, graph = self.debate
        return {
            "dataset": dataset,
            "method": method,
            "item": item,
            "graph": graph,
            "honest_agent": self.honest_agent,
            "insider": self.insider,
            "round": self.round_position,
        }


def shadow_events(debate: Debate, *, require_failure: bool = True) -> list[ShadowEvent]:
    """Honest agents converted by a not-yet-flagged adjacent insider."""
    if len(debate.rounds) < 2 or debate.attack_target is None:
        return []
    target = debate.attack_target
    if _same(target, debate.gold, debate.dataset):
        return []  # self-sabotaged question: adopting the target is not contamination
    if require_failure and score_debate(debate).g_del:
        return []
    if not debate.adjacency:
        return []
    terminal = debate.rounds[-1]
    eligible = {
        j
        for j, flag in enumerate(terminal.flags)
        if not flag and j not in debate.insiders
    }
    events: list[ShadowEvent] = []
    for position in range(1, len(debate.rounds)):
        before = debate.rounds[position - 1]
        after = debate.rounds[position]
        for honest in sorted(eligible):
            if not _same(before.votes[honest], debate.gold, debate.dataset):
                continue
            if not _same(after.votes[honest], target, debate.dataset):
                continue
            if _same(before.votes[honest], after.votes[honest], debate.dataset):
                continue
            for insider in debate.insiders:
                if insider == honest or not debate.adjacency[insider][honest]:
                    continue
                if not _same(before.votes[insider], target, debate.dataset):
                    continue
                if any(debate.rounds[k].flags[insider] for k in range(position)):
                    continue  # already flagged before the message was read
                events.append(
                    ShadowEvent(
                        debate=debate.key,
                        honest_agent=honest,
                        insider=insider,
                        round_position=position,
                    )
                )
    return events


def _same(a: str | None, b: str | None, dataset: str) -> bool:
    if a is None or b is None:
        return False
    return a == b if dataset == "GSM8K" else str(a).upper() == str(b).upper()


# --------------------------------------------------------------------------- #
# Oracle Paradox decomposition (Task 1)
# --------------------------------------------------------------------------- #
ORACLE_SLICES = (
    "SELF_SABOTAGED_64",
    "TRUE_ADVERSARIAL_236",
    "GSM8K_100",
    "ALL",
)


def oracle_flags(debate: Debate) -> tuple[int, ...]:
    """True-insider oracle: flag exactly the agents the archive knows are insiders."""
    insiders = set(debate.insiders)
    return tuple(1 if i in insiders else 0 for i in range(debate.n_agents))


def oracle_delivery(debate: Debate):
    return deliver(debate.votes, oracle_flags(debate), debate.gold, debate.dataset)


def oracle_slice(debate: Debate) -> str:
    if debate.attack_target is not None and _same(
        debate.attack_target, debate.gold, debate.dataset
    ):
        return "SELF_SABOTAGED_64"
    if debate.dataset == "GSM8K":
        return "GSM8K_100"
    return "TRUE_ADVERSARIAL_236"


def _unfiltered_delivery(debate: Debate):
    flags = tuple(0 for _ in range(debate.n_agents))
    return deliver(debate.votes, flags, debate.gold, debate.dataset)


def _classify_discordance(debate: Debate, flags: Sequence[int]) -> str:
    """Type I / II / III for a case where the detector succeeds and the oracle fails."""
    insiders = set(debate.insiders)
    if debate.attack_target is not None and _same(
        debate.attack_target, debate.gold, debate.dataset
    ):
        if any(
            flags[i] == 0 and _same(debate.votes[i], debate.gold, debate.dataset)
            for i in insiders
        ):
            return "I"
    events = shadow_events(debate, require_failure=False)
    poisoned = {event.honest_agent for event in events}
    if any(flags[j] for j in poisoned):
        return "II"
    if any(
        flags[j]
        and j not in insiders
        and j not in poisoned
        and not _same(debate.votes[j], debate.gold, debate.dataset)
        for j in range(debate.n_agents)
    ):
        return "III"
    return "other"


def _arm_delivery(debate: Debate, name: str, extra_flags):
    if name == "Unfiltered":
        return _unfiltered_delivery(debate)
    if name == "Oracle":
        return oracle_delivery(debate)
    if extra_flags is not None and name in extra_flags:
        flags = extra_flags[name]
    else:
        flags = debate.flags
    return deliver(debate.votes, flags, debate.gold, debate.dataset)


def decompose_oracle_paradox(
    debates: Sequence[Debate],
    *,
    extra_arms: dict[str, dict[tuple, Sequence[int]]] | None = None,
    methods: Sequence[str] = DETECTORS,
) -> dict:
    """Explain why the true-insider oracle trails the best learned detector.

    Three panels are produced:

    1. delivered accuracy of every arm on the three attack-validity slices;
    2. within-stratum oracle vs detector accuracy (the paired comparison);
    3. a Type I/II/III decomposition of every debate where a detector is
       delivered-correct and the oracle is delivered-wrong.

    The key finding is compositional: the pooled oracle number is dragged down
    by the conversation sets it is pooled over, not by the oracle losing to
    ``XG-Guard`` on the debates where the two can be compared.
    """
    detector_debates = [d for d in debates if d.method in methods]
    arm_names = ["Unfiltered", "Oracle", *methods]
    if extra_arms:
        arm_names.extend(extra_arms)

    by_slice: dict[str, dict[str, dict]] = {name: {} for name in ORACLE_SLICES}
    for arm in arm_names:
        # Baselines are evaluated on their own 1,600 debates (a baseline flag
        # vector is only defined on its own conversation set); the oracle, the
        # unfiltered tally and the guard arms are pooled over all 9,600.
        if arm in methods:
            arm_debates = [d for d in detector_debates if d.method == arm]
            flags_for_arm = None
        else:
            arm_debates = detector_debates
            flags_for_arm = extra_arms.get(arm) if extra_arms else None
        for slice_name in ORACLE_SLICES:
            subset = (
                list(arm_debates)
                if slice_name == "ALL"
                else [d for d in arm_debates if oracle_slice(d) == slice_name]
            )
            delivered = 0
            released = 0
            for debate in subset:
                delivery = _arm_delivery(debate, arm, flags_for_arm)
                delivered += int(delivery.correct)
                released += int(check(plurality(list(debate.votes)),
                                      debate.gold, debate.dataset))
            n = len(subset)
            by_slice[slice_name][arm] = {
                "debates": n,
                "g_del_percent": 100.0 * delivered / max(n, 1),
                "g_release_percent": 100.0 * released / max(n, 1),
            }

    within_stratum: dict[str, dict] = {}
    for method in methods:
        subset = [d for d in detector_debates if d.method == method]
        oracle = sum(oracle_delivery(d).correct for d in subset)
        detector = sum(score_debate(d).g_del for d in subset)
        n = len(subset)
        within_stratum[method] = {
            "debates": n,
            "oracle_percent": 100.0 * oracle / max(n, 1),
            "detector_percent": 100.0 * detector / max(n, 1),
            "delta_pp": 100.0 * (oracle - detector) / max(n, 1),
        }

    discordance: dict[str, dict] = {}
    types: dict[str, int] = {name: 0 for name in ("I", "II", "III", "other")}
    examples: list[dict] = []
    for method in methods:
        subset = [d for d in detector_debates if d.method == method]
        cell = {"detector_only": 0, "oracle_only": 0, "types": dict(types)}
        for debate in subset:
            det_ok = score_debate(debate).g_del
            oracle_ok = oracle_delivery(debate).correct
            if det_ok and not oracle_ok:
                cell["detector_only"] += 1
                kind = _classify_discordance(debate, debate.flags)
                cell["types"][kind] += 1
                types[kind] += 1
                if len(examples) < 12:
                    examples.append(
                        {
                            "dataset": debate.dataset,
                            "item": debate.item,
                            "graph": debate.graph,
                            "method": method,
                            "type": kind,
                            "slice": oracle_slice(debate),
                            "flags": [int(f) for f in debate.flags],
                        }
                    )
            elif oracle_ok and not det_ok:
                cell["oracle_only"] += 1
        cell["net_pp"] = 100.0 * (cell["oracle_only"] - cell["detector_only"]) / max(
            len(subset), 1
        )
        discordance[method] = cell

    xg = [d for d in detector_debates if d.method == "XG-Guard"]
    xg_table = {"both": 0, "xg_only": 0, "oracle_only": 0, "neither": 0}
    for debate in xg:
        det_ok = score_debate(debate).g_del
        oracle_ok = oracle_delivery(debate).correct
        key = (
            "both" if det_ok and oracle_ok
            else "xg_only" if det_ok
            else "oracle_only" if oracle_ok
            else "neither"
        )
        xg_table[key] += 1

    return {
        "by_slice": by_slice,
        "within_stratum": within_stratum,
        "discordance": discordance,
        "discordance_types": types,
        "examples": examples,
        "xg_oracle_table": xg_table,
        "verdict": (
            "The Oracle Paradox is a composition artifact: pooled over six "
            "conversation sets the oracle scores below XG-Guard, but on XG-Guard's "
            "own debates the two differ by only "
            f"{within_stratum.get('XG-Guard', {}).get('delta_pp', 0.0):+.2f} pp "
            f"({xg_table['xg_only']} XG-only vs {xg_table['oracle_only']} oracle-only "
            "debates). Type I/II/III mechanisms therefore explain a handful of "
            "debates, not the headline gap."
        ),
    }


def shadow_summary(
    debates: Sequence[Debate], *, require_failure: bool = True
) -> dict:
    """Pre-exclusion shadow contamination rates, overall and by cell."""
    considered = [
        d
        for d in debates
        if len(d.rounds) >= 2
        and d.attack_target is not None
        and not _same(d.attack_target, d.gold, d.dataset)
    ]
    events: list[ShadowEvent] = []
    contaminated: set[tuple] = set()
    by_task: dict[str, dict[str, int]] = {}
    by_graph: dict[str, dict[str, int]] = {}
    by_method: dict[str, dict[str, int]] = {}
    by_round: dict[int, dict[str, int]] = {}
    failures: set[tuple] = set()

    control_events: list[ShadowEvent] = []
    for debate in considered:
        if not score_debate(debate).g_del:
            failures.add(debate.key)
    for debate in considered:
        found = shadow_events(debate, require_failure=require_failure)
        if debate.is_control:
            control_events.extend(found)
            if found:
                contaminated.add(debate.key)
            continue  # the diagnostic cells describe detector debates
        events.extend(found)
        if found:
            contaminated.add(debate.key)
        for table, key in (
            (by_task, debate.dataset),
            (by_graph, debate.graph),
            (by_method, debate.method),
        ):
            cell = table.setdefault(key, {"debates": 0, "contaminated": 0})
            cell["debates"] += 1
            cell["contaminated"] += int(bool(found))
        for position in {event.round_position for event in found}:
            cell = by_round.setdefault(position, {"events": 0})
            cell["events"] += 1

    def rates(table: dict[str, dict[str, int]]) -> dict[str, dict[str, float]]:
        return {
            key: {
                "debates": cell["debates"],
                "contaminated": cell["contaminated"],
                "rate_percent": 100.0 * cell["contaminated"] / max(cell["debates"], 1),
            }
            for key, cell in sorted(table.items())
        }

    detector = [d for d in considered if not d.is_control]
    control = [d for d in considered if d.is_control]
    detector_hits = sum(1 for d in detector if d.key in contaminated)
    control_hits = sum(1 for d in control if d.key in contaminated)
    detector_considered = [d for d in considered if not d.is_control]
    return {
        "require_delivered_failure": require_failure,
        "debates_considered": len(considered),
        "detector_debates": len(detector),
        "control_debates": len(control),
        "events": len(events),
        "control_events": len(control_events),
        "contaminated_debates": len(contaminated),
        "contamination_rate_percent": 100.0
        * len(contaminated)
        / max(len(detector_considered), 1),
        "detector_rate_percent": 100.0 * detector_hits / max(len(detector), 1),
        "control_rate_percent": 100.0 * control_hits / max(len(control), 1),
        "mean_events_per_contaminated_debate": len(events) / max(len(contaminated), 1),
        "delivered_failures": len(failures),
        "by_task": rates(by_task),
        "by_graph": rates(by_graph),
        "by_method": rates(by_method),
        "debates_with_event_by_round": {
            f"round_{position}": cell["events"] for position, cell in sorted(by_round.items())
        },
        "examples": [event.as_dict() for event in events[:8]],
    }
