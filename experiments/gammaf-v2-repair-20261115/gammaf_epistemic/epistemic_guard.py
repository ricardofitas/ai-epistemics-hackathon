"""``EpistemicGuard``: a training-free graph-epistemic anomaly detector.

Three signals are computed per agent from the executed vote trajectory and the
debate graph, fused by a calibrated logistic, and exposed in two modes:

* ``EpistemicGuard-Hard`` -- binary flags compatible with the GAMMAF interface
  (top-3 cap, reversible benign-agreement relaxation), graded through the
  standard ``a_del = pi(v_U)``.
* ``EpistemicGuard-Soft`` -- continuous epistemic trust weights, so no honest
  voter is ever fully excluded; the delivered answer is the weighted plurality.

No gold labels, detector outputs or model weights are used at inference time.
"""

from __future__ import annotations

import collections
import itertools
from dataclasses import dataclass, field
from typing import Sequence

import numpy as np

from .data import DETECTORS, N_AGENTS, Debate
from .gammaf_clean import ABSTAIN, Delivery, check, deliver, plurality

SIGNAL_NAMES = ("stubbornness", "bloc", "net")

DEFAULT_TOP_K = 3
DEFAULT_GAMMA = 0.7


@dataclass(frozen=True)
class GuardParams:
    """Fusion and aggregation hyperparameters (tuned on a question split)."""

    a1: float = 2.0
    a2: float = 2.5
    a3: float = 1.5
    b: float = 2.5
    tau: float = 0.5
    lam: float = 2.0
    eta: float = 0.5
    top_k: int = DEFAULT_TOP_K
    gamma: float = DEFAULT_GAMMA
    a4: float = 0.0  # optional ensemble prior weight

    def as_dict(self) -> dict:
        return {
            "a1": self.a1,
            "a2": self.a2,
            "a3": self.a3,
            "b": self.b,
            "tau": self.tau,
            "lam": self.lam,
            "eta": self.eta,
            "top_k": self.top_k,
            "gamma": self.gamma,
            "a4": self.a4,
        }


# --------------------------------------------------------------------------- #
# Graph helpers
# --------------------------------------------------------------------------- #
def adjacency_matrix(debate: Debate) -> np.ndarray:
    if debate.adjacency:
        matrix = np.asarray(debate.adjacency, dtype=int)
    else:
        matrix = np.ones((debate.n_agents, debate.n_agents), dtype=int)
    symmetric = ((matrix + matrix.T) > 0).astype(int)
    np.fill_diagonal(symmetric, 0)
    return symmetric


def distance_matrix(adjacency: np.ndarray) -> np.ndarray:
    n = len(adjacency)
    dist = np.full((n, n), np.inf)
    for source in range(n):
        dist[source, source] = 0.0
        frontier = [source]
        while frontier:
            nxt: list[int] = []
            for node in frontier:
                for neighbour in np.flatnonzero(adjacency[node]):
                    if np.isinf(dist[source, neighbour]):
                        dist[source, neighbour] = dist[source, node] + 1.0
                        nxt.append(int(neighbour))
            frontier = nxt
    return dist


# --------------------------------------------------------------------------- #
# The three epistemic anomaly signals
# --------------------------------------------------------------------------- #
def stubbornness_signal(debate: Debate) -> np.ndarray:
    """Cumulative persistence under local disagreement, in [0, 1]."""
    n = debate.n_agents
    score = np.zeros(n)
    rounds = debate.rounds
    if len(rounds) < 2:
        return score
    adjacency = adjacency_matrix(debate)
    for position in range(1, len(rounds)):
        previous = rounds[position - 1].votes
        current = rounds[position].votes
        for agent in range(n):
            neighbours = np.flatnonzero(adjacency[agent])
            if len(neighbours) == 0:
                continue
            disagreement = float(
                np.mean([previous[k] != previous[agent] for k in neighbours])
            )
            stayed = 1.0 if current[agent] == previous[agent] else 0.0
            score[agent] += stayed * disagreement
    score /= len(rounds) - 1
    return np.clip(score, 0.0, 1.0)


def bloc_signal(debate: Debate) -> np.ndarray:
    """Coordinated minority blocs that cannot have met through the graph."""
    n = debate.n_agents
    score = np.zeros(n)
    rounds = debate.rounds
    if not rounds:
        return score
    adjacency = adjacency_matrix(debate)
    dist = distance_matrix(adjacency)
    for position, round_obj in enumerate(rounds):
        counts = collections.Counter(round_obj.votes)
        if not counts:
            continue
        top = counts.most_common(1)[0][0]
        for answer, size in counts.items():
            if answer == top or not 2 <= size <= 4:
                continue
            members = [i for i in range(n) if round_obj.votes[i] == answer]
            pairs = list(itertools.combinations(members, 2))
            if not pairs:
                continue
            spread = float(np.mean([dist[i][j] for i, j in pairs]))
            if spread > position + 1:  # round number is 1-based
                for member in members:
                    score[member] += 1.0
    score /= len(rounds)
    return np.clip(score, 0.0, 1.0)


def _influence_edges(debate: Debate, position: int) -> set[tuple[int, int]]:
    adjacency = adjacency_matrix(debate)
    previous = debate.rounds[position - 1].votes
    current = debate.rounds[position].votes
    edges: set[tuple[int, int]] = set()
    for target in range(debate.n_agents):
        if current[target] == previous[target]:
            continue
        for source in range(debate.n_agents):
            if source == target or not adjacency[source][target]:
                continue
            if current[target] == previous[source] and previous[source] != previous[target]:
                edges.add((source, target))
    return edges


def net_signal(debate: Debate, gamma: float = DEFAULT_GAMMA) -> np.ndarray:
    """Genealogical taint: sources of influence score 1, echoes attenuate by ``gamma``.

    Taint persists across rounds.  A node that was already infected as an echo
    cannot be re-promoted to a source later, which is the provenance rule: a
    genuine secondary infection needs a suspicious neighbour one step earlier.
    """
    n = debate.n_agents
    taint = np.zeros(n)
    if len(debate.rounds) < 2:
        return taint
    for position in range(1, len(debate.rounds)):
        edges = _influence_edges(debate, position)
        if not edges:
            continue
        out_degree = collections.Counter(source for source, _ in edges)
        in_degree = collections.Counter(target for _, target in edges)
        for source in out_degree:
            if taint[source] == 0.0 and in_degree[source] == 0:
                taint[source] = 1.0
        for _ in range(n):
            changed = False
            for source, target in edges:
                candidate = taint[source] * gamma
                if candidate > taint[target] + 1e-12:
                    taint[target] = candidate
                    changed = True
            if not changed:
                break
    return np.clip(taint, 0.0, 1.0)


def signals(debate: Debate, gamma: float = DEFAULT_GAMMA) -> tuple[np.ndarray, ...]:
    return (
        stubbornness_signal(debate),
        bloc_signal(debate),
        net_signal(debate, gamma),
    )


# --------------------------------------------------------------------------- #
# Fusion and aggregation on a single debate
# --------------------------------------------------------------------------- #
def _sigmoid(x: np.ndarray | float) -> np.ndarray | float:
    return 1.0 / (1.0 + np.exp(-x))


def fuse(
    stub: np.ndarray,
    bloc: np.ndarray,
    net: np.ndarray,
    params: GuardParams,
    prior: np.ndarray | None = None,
) -> np.ndarray:
    logit = params.a1 * stub + params.a2 * bloc + params.a3 * net - params.b
    if prior is not None and params.a4:
        logit = logit + params.a4 * prior
    return np.asarray(_sigmoid(logit), dtype=float)


def benign_agreement(debate: Debate) -> np.ndarray:
    """Agents voting with the round plurality for the last two executed rounds."""
    mask = np.zeros(debate.n_agents, dtype=bool)
    if len(debate.rounds) < 2:
        return mask
    keep = np.ones(debate.n_agents, dtype=bool)
    for round_obj in debate.rounds[-2:]:
        top = plurality(list(round_obj.votes))
        keep &= np.array([vote == top for vote in round_obj.votes], dtype=bool)
    return keep


def hard_flags(
    debate: Debate, p: np.ndarray, params: GuardParams
) -> tuple[np.ndarray, np.ndarray]:
    """Threshold, cap at top-K, then relax flags with benign agreement."""
    n = debate.n_agents
    if len(debate.rounds) < 2:
        return np.zeros(n, dtype=int), np.zeros(n, dtype=bool)
    order = np.argsort(-p, kind="stable")
    rank = np.empty(n, dtype=int)
    rank[order] = np.arange(n)
    flags = (p >= params.tau) & (rank < params.top_k)
    flags &= ~benign_agreement(debate)
    if flags.all():
        flags[int(np.argmin(p))] = False
    if not flags.any():
        flags = np.zeros(n, dtype=bool)
    return flags.astype(int), rank < params.top_k


def shadow_taint(debate: Debate, p: np.ndarray, params: GuardParams) -> np.ndarray:
    """Honest agents whose terminal vote echoed a high-suspicion neighbour."""
    taint = np.zeros(debate.n_agents)
    if len(debate.rounds) < 2:
        return taint
    previous = debate.rounds[-2].votes
    current = debate.rounds[-1].votes
    adjacency = adjacency_matrix(debate)
    for target in range(debate.n_agents):
        if current[target] == previous[target]:
            continue
        for source in range(debate.n_agents):
            if source == target or not adjacency[source][target]:
                continue
            if p[source] < params.tau:
                continue
            if current[target] == previous[source] and previous[source] != previous[target]:
                taint[target] = 1.0
                break
    return taint


def soft_weights(debate: Debate, p: np.ndarray, params: GuardParams) -> np.ndarray:
    taint = shadow_taint(debate, p, params)
    weights = np.power(np.clip(1.0 - p, 0.0, 1.0), params.lam)
    weights *= 1.0 - params.eta * taint
    return np.clip(weights, 0.0, 1.0)


def soft_delivery(
    debate: Debate, p: np.ndarray, params: GuardParams
) -> tuple[Delivery, np.ndarray]:
    weights = soft_weights(debate, p, params)
    totals: dict[str, float] = {}
    first_seen: dict[str, int] = {}
    for agent, vote in enumerate(debate.votes):
        totals[vote] = totals.get(vote, 0.0) + float(weights[agent])
        first_seen.setdefault(vote, agent)
    if not totals or max(totals.values()) <= 0.0:
        return Delivery(ABSTAIN, False, (), "soft_abstain", True), weights
    answer = min(totals, key=lambda option: (-totals[option], first_seen[option]))
    return Delivery(answer, check(answer, debate.gold, debate.dataset), (), None, False), weights


# --------------------------------------------------------------------------- #
# Vectorized dataset evaluation (used for tuning and the leaderboard)
# --------------------------------------------------------------------------- #
class GuardData:
    """Pre-computed signals for a debate collection, in a scoring-friendly form."""

    def __init__(self, debates: Sequence[Debate], gamma: float = DEFAULT_GAMMA):
        self.debates = list(debates)
        self.n = len(self.debates)
        self.vote_ids = np.zeros((self.n, N_AGENTS), dtype=np.int64)
        self.cat_correct = np.zeros((self.n, N_AGENTS), dtype=bool)
        self.cat_raw: list[list[str]] = [[""] * N_AGENTS for _ in range(self.n)]
        self.stub = np.zeros((self.n, N_AGENTS))
        self.bloc = np.zeros((self.n, N_AGENTS))
        self.net = np.zeros((self.n, N_AGENTS))
        self.benign = np.zeros((self.n, N_AGENTS), dtype=bool)
        self.taint_source = np.zeros((self.n, N_AGENTS, N_AGENTS), dtype=bool)
        self.has_trajectory = np.zeros(self.n, dtype=bool)
        for row, debate in enumerate(self.debates):
            mapping: dict[str, int] = {}
            for agent, vote in enumerate(debate.votes):
                if vote not in mapping:
                    category = len(mapping)
                    mapping[vote] = category
                    self.cat_raw[row][category] = vote
                    self.cat_correct[row, category] = check(
                        vote, debate.gold, debate.dataset
                    )
                self.vote_ids[row, agent] = mapping[vote]
            if len(debate.rounds) >= 2:
                self.has_trajectory[row] = True
                stub, bloc, net = signals(debate, gamma)
                self.stub[row] = stub
                self.bloc[row] = bloc
                self.net[row] = net
                self.benign[row] = benign_agreement(debate)
                previous = debate.rounds[-2].votes
                current = debate.rounds[-1].votes
                adjacency = adjacency_matrix(debate)
                for target in range(N_AGENTS):
                    if current[target] == previous[target]:
                        continue
                    for source in range(N_AGENTS):
                        if source == target or not adjacency[source][target]:
                            continue
                        if (
                            current[target] == previous[source]
                            and previous[source] != previous[target]
                        ):
                            self.taint_source[row, target, source] = True

    # -- helpers ---------------------------------------------------------- #
    def answer(self, row: int, category: int) -> str:
        return self.cat_raw[row][int(category)]

    def _one_hot(self) -> np.ndarray:
        categories = np.arange(N_AGENTS)[None, None, :]
        return self.vote_ids[:, :, None] == categories

    def _plurality(self, one_hot: np.ndarray, mask: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        weights = one_hot & mask[:, :, None]
        counts = weights.sum(axis=1)
        positions = np.arange(N_AGENTS)[None, :, None]
        first = np.where(weights, positions, N_AGENTS).min(axis=1)
        chosen = np.lexsort((first, -counts), axis=1)[:, 0]
        return chosen, counts

    # -- scoring ---------------------------------------------------------- #
    def suspicion(self, params: GuardParams, prior: np.ndarray | None = None) -> np.ndarray:
        p = fuse(self.stub, self.bloc, self.net, params, prior)
        p[~self.has_trajectory] = 0.0
        return p

    def score_hard(
        self, params: GuardParams, prior: np.ndarray | None = None
    ) -> dict:
        p = self.suspicion(params, prior)
        order = np.argsort(-p, axis=1, kind="stable")
        rank = np.empty_like(order)
        rows = np.arange(self.n)[:, None]
        rank[rows, order] = np.arange(N_AGENTS)[None, :]
        flags = (p >= params.tau) & (rank < params.top_k)
        flags &= ~self.benign
        all_flagged = flags.all(axis=1)
        if all_flagged.any():
            flags[all_flagged, np.argmin(p[all_flagged], axis=1)] = False
        flags[~self.has_trajectory] = False
        one_hot = self._one_hot()
        chosen, counts = self._plurality(one_hot, ~flags)
        correct = self.cat_correct[rows[:, 0], chosen]
        no_eligible = (~flags).sum(axis=1) == 0
        correct = correct & ~no_eligible
        answers = [self.answer(row, chosen[row]) for row in range(self.n)]
        return {
            "p": p,
            "flags": flags.astype(int),
            "answers": answers,
            "correct": correct,
            "accuracy_percent": 100.0 * float(correct.mean()) if self.n else 0.0,
            "mean_flags": float(flags.sum(axis=1).mean()) if self.n else 0.0,
            "empty_eligible": int(no_eligible.sum()),
        }

    def score_soft(
        self, params: GuardParams, prior: np.ndarray | None = None
    ) -> dict:
        p = self.suspicion(params, prior)
        taint = (
            (p[:, None, :] >= params.tau) & self.taint_source
        ).any(axis=2).astype(float)
        weights = np.power(np.clip(1.0 - p, 0.0, 1.0), params.lam)
        weights *= 1.0 - params.eta * taint
        weights = np.clip(weights, 0.0, 1.0)
        one_hot = self._one_hot()
        weighted = (one_hot * weights[:, :, None]).sum(axis=1)
        live = weights[:, :, None] > 0
        positions = np.arange(N_AGENTS)[None, :, None]
        first = np.where(one_hot & live, positions, N_AGENTS).min(axis=1)
        chosen = np.lexsort((first, -weighted), axis=1)[:, 0]
        rows = np.arange(self.n)
        correct = self.cat_correct[rows, chosen]
        abstain = weights.sum(axis=1) <= 0
        correct = correct & ~abstain
        answers = [
            ABSTAIN if abstain[row] else self.answer(row, chosen[row])
            for row in range(self.n)
        ]
        return {
            "p": p,
            "weights": weights,
            "answers": answers,
            "correct": correct,
            "accuracy_percent": 100.0 * float(correct.mean()) if self.n else 0.0,
            "mean_flags": float((p >= params.tau).sum(axis=1).mean()) if self.n else 0.0,
            "empty_eligible": int(abstain.sum()),
        }


# --------------------------------------------------------------------------- #
# Tuner / predictor
# --------------------------------------------------------------------------- #
A1_GRID = (0.0, 1.0, 2.0, 3.0)
A2_GRID = (0.0, 1.0, 2.0, 4.0)
A3_GRID = (0.0, 0.5, 1.0, 2.0)
B_GRID = (1.0, 2.0, 3.0, 4.0)
TAU_GRID = (0.35, 0.5, 0.65)
LAMBDA_GRID = (0.5, 1.0, 2.0, 3.0)
ETA_GRID = (0.0, 0.3, 0.6, 0.9)


@dataclass
class GuardTuning:
    params: GuardParams
    tune_accuracy_percent: float
    tune_accuracy_soft_percent: float
    evaluated: int
    split_size: int


class EpistemicGuard:
    """Training-free detector with hard (GAMMAF-compatible) and soft modes."""

    def __init__(self, params: GuardParams | None = None):
        self.params = params or GuardParams()
        self.tuning: GuardTuning | None = None

    # -- fitting ---------------------------------------------------------- #
    def fit(
        self,
        debates: Sequence[Debate],
        *,
        prior: np.ndarray | None = None,
        ensemble_weight: float = 0.0,
    ) -> GuardTuning:
        data = GuardData(debates, self.params.gamma)
        best = None
        evaluated = 0
        for a1, a2, a3, b in itertools.product(A1_GRID, A2_GRID, A3_GRID, B_GRID):
            base = GuardParams(
                a1=a1, a2=a2, a3=a3, b=b, top_k=self.params.top_k,
                gamma=self.params.gamma, a4=ensemble_weight,
            )
            for tau in TAU_GRID:
                params = GuardParams(**{**base.as_dict(), "tau": tau})
                result = data.score_hard(params, prior)
                evaluated += 1
                key = (result["accuracy_percent"], -params.b, -params.tau)
                if best is None or key > best[0]:
                    best = (key, params, result["accuracy_percent"])
        assert best is not None
        _, best_hard, hard_accuracy = best
        best_soft = None
        for lam, eta in itertools.product(LAMBDA_GRID, ETA_GRID):
            params = GuardParams(**{**best_hard.as_dict(), "lam": lam, "eta": eta})
            result = data.score_soft(params, prior)
            evaluated += 1
            key = (result["accuracy_percent"], -params.eta)
            if best_soft is None or key > best_soft[0]:
                best_soft = (key, params, result["accuracy_percent"])
        assert best_soft is not None
        _, best_params, soft_accuracy = best_soft
        self.params = best_params
        self.tuning = GuardTuning(
            params=best_params,
            tune_accuracy_percent=hard_accuracy,
            tune_accuracy_soft_percent=soft_accuracy,
            evaluated=evaluated,
            split_size=len(debates),
        )
        return self.tuning

    # -- prediction ------------------------------------------------------- #
    def predict_hard(self, debates: Sequence[Debate], *, prior: np.ndarray | None = None) -> dict:
        return GuardData(debates, self.params.gamma).score_hard(self.params, prior)

    def predict_soft(self, debates: Sequence[Debate], *, prior: np.ndarray | None = None) -> dict:
        return GuardData(debates, self.params.gamma).score_soft(self.params, prior)

    # -- single-debate API ------------------------------------------------ #
    def flags(self, debate: Debate) -> np.ndarray:
        stub, bloc, net = signals(debate, self.params.gamma)
        p = np.asarray(fuse(stub, bloc, net, self.params), dtype=float)
        if len(debate.rounds) < 2:
            return np.zeros(debate.n_agents, dtype=int)
        flags, _ = hard_flags(debate, p, self.params)
        return flags

    def suspicion(self, debate: Debate) -> np.ndarray:
        stub, bloc, net = signals(debate, self.params.gamma)
        p = np.asarray(fuse(stub, bloc, net, self.params), dtype=float)
        if len(debate.rounds) < 2:
            p = np.zeros(debate.n_agents)
        return p

    def deliver_hard(self, debate: Debate) -> Delivery:
        flags = self.flags(debate)
        eligible = tuple(i for i, flag in enumerate(flags) if not flag)
        if not eligible:
            return Delivery(ABSTAIN, False, (), "strict_abstain", True)
        answer = plurality([debate.votes[i] for i in eligible])
        assert answer is not None
        return Delivery(answer, check(answer, debate.gold, debate.dataset), eligible, None, False)

    def deliver_soft(self, debate: Debate) -> Delivery:
        p = self.suspicion(debate)
        delivery, _ = soft_delivery(debate, p, self.params)
        return delivery


# --------------------------------------------------------------------------- #
# Epistemic rollback: cure honest voters poisoned by an excluded neighbour
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class PoisonLink:
    """An honest agent's terminal vote copied from a flagged neighbour."""

    agent: int
    insider: int
    round_position: int
    clean_vote: str


def poison_links(
    debate: Debate, flags: Sequence[int]
) -> list[PoisonLink]:
    """First vote switch of each unflagged honest agent that copied a flagged neighbour.

    Uses only observable trajectories, the graph and the detector's own flags.
    """
    if len(debate.rounds) < 2:
        return []
    adjacency = adjacency_matrix(debate)
    insiders = set(debate.insiders)
    links: dict[int, PoisonLink] = {}
    for position in range(1, len(debate.rounds)):
        before = debate.rounds[position - 1].votes
        after = debate.rounds[position].votes
        for agent in range(debate.n_agents):
            if agent in links or agent in insiders or flags[agent]:
                continue
            if after[agent] == before[agent]:
                continue
            for source in range(debate.n_agents):
                if source == agent or not adjacency[source][agent] or not flags[source]:
                    continue
                if after[agent] == before[source] and before[source] != before[agent]:
                    links[agent] = PoisonLink(
                        agent=agent,
                        insider=source,
                        round_position=position,
                        clean_vote=before[agent],
                    )
                    break
    return [links[agent] for agent in sorted(links)]


def rollback_votes(
    debate: Debate, flags: Sequence[int]
) -> tuple[tuple[str, ...], list[PoisonLink]]:
    """Replace each poisoned terminal vote with its pre-contact belief."""
    links = poison_links(debate, flags)
    votes = list(debate.votes)
    for link in links:
        votes[link.agent] = link.clean_vote
    return tuple(votes), links


def rollback_delivery(
    debate: Debate, flags: Sequence[int]
) -> tuple[Delivery, tuple[str, ...], list[PoisonLink]]:
    votes, links = rollback_votes(debate, flags)
    delivery = deliver(votes, flags, debate.gold, debate.dataset)
    return delivery, votes, links


# --------------------------------------------------------------------------- #
# EpistemicGuard-Ensemble: false-positive rehabilitation + rollback
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class EnsembleParams:
    """Rehabilitation and missed-insider thresholds (tuned on the tune split)."""

    tau_rehab: float = 0.40
    tau_high: float = 0.65
    top_k: int = DEFAULT_TOP_K

    def as_dict(self) -> dict:
        return {
            "tau_rehab": self.tau_rehab,
            "tau_high": self.tau_high,
            "top_k": self.top_k,
        }


@dataclass
class EnsembleTuning:
    params: EnsembleParams
    tune_accuracy_percent: float
    by_method: dict[str, float]
    split_size: int
    evaluated: int


def ensemble_flags(
    debate: Debate,
    p: np.ndarray,
    base_flags: Sequence[int],
    params: EnsembleParams,
    *,
    stub: np.ndarray | None = None,
    bloc: np.ndarray | None = None,
) -> np.ndarray:
    """Rehabilitate benign flagged agents, then flag high-suspicion missed ones."""
    if stub is None or bloc is None:
        stub, bloc, _ = signals(debate, DEFAULT_GAMMA)
    base = np.asarray(base_flags, dtype=bool).copy()
    flags = base.copy()
    flags &= ~((stub < params.tau_rehab) & (bloc < params.tau_rehab))
    flags |= p >= params.tau_high
    if flags.sum() > params.top_k:
        order = np.argsort(-p, kind="stable")
        keep = np.zeros(debate.n_agents, dtype=bool)
        keep[order[: params.top_k]] = True
        flags &= keep
    if flags.all():
        flags[int(np.argmin(p))] = False
    return flags.astype(int)


def ensemble_result(
    debate: Debate,
    p: np.ndarray,
    base_flags: Sequence[int],
    params: EnsembleParams,
    *,
    stub: np.ndarray | None = None,
    bloc: np.ndarray | None = None,
) -> dict:
    flags = ensemble_flags(debate, p, base_flags, params, stub=stub, bloc=bloc)
    delivery, votes, links = rollback_delivery(debate, flags)
    return {
        "flags": flags,
        "votes": votes,
        "delivery": delivery,
        "links": links,
        "rehabilitated": int(
            sum(1 for i, flag in enumerate(base_flags) if flag and not flags[i])
        ),
        "missed_flagged": int(
            sum(1 for i, flag in enumerate(base_flags) if not flag and flags[i])
        ),
    }


REHAB_GRID = (0.25, 0.40, 0.55)
HIGH_GRID = (0.55, 0.70, 0.85)


def _equal_stratum_mean(debates: Sequence[Debate], correct: np.ndarray) -> float:
    strata: dict[str, list[float]] = {}
    for debate, ok in zip(debates, correct):
        strata.setdefault(debate.method, []).append(float(ok))
    values = [sum(v) / len(v) for v in strata.values() if v]
    return 100.0 * sum(values) / max(len(values), 1)


def tune_ensemble(
    tune_debates: Sequence[Debate],
    guard: EpistemicGuard,
) -> EnsembleTuning:
    """Grid-search the rehabilitation/missed-insider thresholds on the tune split."""
    data = GuardData(tune_debates, guard.params.gamma)
    p = data.suspicion(guard.params)
    base = [debate.flags for debate in tune_debates]
    best: tuple[tuple[float, float, float], EnsembleParams, np.ndarray] | None = None
    evaluated = 0
    for tau_rehab, tau_high in itertools.product(REHAB_GRID, HIGH_GRID):
        params = EnsembleParams(
            tau_rehab=tau_rehab, tau_high=tau_high, top_k=guard.params.top_k
        )
        correct = np.zeros(len(tune_debates), dtype=bool)
        for row, debate in enumerate(tune_debates):
            result = ensemble_result(
                debate,
                p[row],
                base[row],
                params,
                stub=data.stub[row],
                bloc=data.bloc[row],
            )
            correct[row] = result["delivery"].correct
        evaluated += 1
        score = _equal_stratum_mean(tune_debates, correct)
        key = (score, -tau_rehab, -tau_high)
        if best is None or key > best[0]:
            best = (key, params, correct)
    assert best is not None
    _, params, correct = best
    strata: dict[str, list[float]] = {}
    for debate, ok in zip(tune_debates, correct):
        strata.setdefault(debate.method, []).append(float(ok))
    return EnsembleTuning(
        params=params,
        tune_accuracy_percent=100.0 * float(correct.mean()),
        by_method={m: 100.0 * sum(v) / len(v) for m, v in strata.items()},
        split_size=len(tune_debates),
        evaluated=evaluated,
    )


def ensemble_evaluate(
    debates: Sequence[Debate],
    guard: EpistemicGuard,
    params: EnsembleParams,
) -> dict:
    """Evaluate the ensemble arm (with rollback) per conversation set."""
    data = GuardData(debates, guard.params.gamma)
    p = data.suspicion(guard.params)
    rows: list[dict] = []
    for row, debate in enumerate(debates):
        result = ensemble_result(
            debate,
            p[row],
            debate.flags,
            params,
            stub=data.stub[row],
            bloc=data.bloc[row],
        )
        delivery = result["delivery"]
        rows.append(
            {
                "method": debate.method,
                "correct": delivery.correct,
                "flags": int(result["flags"].sum()),
                "rehabilitated": result["rehabilitated"],
                "missed_flagged": result["missed_flagged"],
                "rolled": len(result["links"]),
            }
        )
    by_method: dict[str, dict] = {}
    for method in sorted({row["method"] for row in rows}):
        subset = [row for row in rows if row["method"] == method]
        by_method[method] = {
            "debates": len(subset),
            "accuracy_percent": 100.0 * sum(row["correct"] for row in subset) / len(subset),
            "mean_flags": sum(row["flags"] for row in subset) / len(subset),
            "rehabilitated": sum(row["rehabilitated"] for row in subset),
            "missed_flagged": sum(row["missed_flagged"] for row in subset),
            "rolled": sum(row["rolled"] for row in subset),
        }
    return {
        "params": params.as_dict(),
        "debates": len(rows),
        "accuracy_percent": 100.0 * sum(row["correct"] for row in rows) / max(len(rows), 1),
        "equal_stratum_percent": _equal_stratum_mean(
            debates, np.array([row["correct"] for row in rows])
        ),
        "by_method": by_method,
    }

