"""EpistemicGuard signal, aggregation and tuning tests."""

from __future__ import annotations

import numpy as np
import pytest

from gammaf_epistemic.epistemic_guard import (
    EpistemicGuard,
    GuardData,
    GuardParams,
    bloc_signal,
    net_signal,
    shadow_taint,
    signals,
    soft_delivery,
    soft_weights,
    stubbornness_signal,
)


def _chain(n=10):
    return [[1 if abs(i - j) == 1 else 0 for j in range(n)] for i in range(n)]


def test_signals_are_bounded_and_finite(debates):
    for debate in [d for d in debates if d.method == "BlindGuard"][:12]:
        stub, bloc, net = signals(debate)
        for signal in (stub, bloc, net):
            assert signal.shape == (10,)
            assert np.all(np.isfinite(signal))
            assert signal.min() >= 0.0 and signal.max() <= 1.0


def test_bloc_signal_detects_a_graphically_impossible_minority(make_debate):
    votes = ["B" if i in (0, 5, 9) else "A" for i in range(10)]
    debate = make_debate(
        votes,
        [0] * 10,
        [votes],
        adjacency=_chain(),
        insiders=(0, 5, 9),
        target="B",
    )
    bloc = bloc_signal(debate)
    assert bloc[0] > 0.0 and bloc[5] > 0.0 and bloc[9] > 0.0
    assert bloc[1] == 0.0 and bloc[4] == 0.0


def test_stubbornness_requires_local_disagreement(make_debate):
    # Everyone agrees, so holding one's position is not stubbornness.
    votes = ["A"] * 10
    debate = make_debate(votes, [0] * 10, [votes, votes], adjacency=_chain())
    assert stubbornness_signal(debate).max() == 0.0
    # Agent 0 keeps B while its only neighbour says A.
    before = ["B", "A", "A", "A", "A", "A", "A", "A", "A", "A"]
    after = ["B", "A", "A", "A", "A", "A", "A", "A", "A", "A"]
    debate2 = make_debate(after, [0] * 10, [before, after], adjacency=_chain(), target="B")
    stub = stubbornness_signal(debate2)
    assert stub[0] == 1.0


def test_net_signal_taints_sources_more_than_echoes(make_debate):
    first = ["B"] + ["A"] * 9
    second = ["B", "B"] + ["A"] * 8
    third = ["B", "B", "B"] + ["A"] * 7
    debate = make_debate(third, [0] * 10, [first, second, third], adjacency=_chain())
    net = net_signal(debate)
    # Agent 0 flipped without a neighbour voting B: it is the source.
    assert net[0] == pytest.approx(1.0)
    # Agent 1 copied agent 0 one hop away, agent 2 copied agent 1.
    assert net[1] == pytest.approx(0.7)
    assert net[2] == pytest.approx(0.49)
    assert net[9] == 0.0


def test_hard_flags_respect_the_top_k_cap(debates):
    guard = EpistemicGuard()
    for debate in [d for d in debates if d.method == "TAM"][:20]:
        flags = guard.flags(debate)
        assert len(flags) == 10
        assert flags.sum() <= 3
        assert set(np.unique(flags)) <= {0, 1}


def test_no_trajectory_means_no_flags(make_debate):
    debate = make_debate(["A"] * 10, [0] * 10, [], adjacency=_chain())
    guard = EpistemicGuard()
    assert guard.flags(debate).sum() == 0
    assert guard.suspicion(debate).max() == 0.0


def test_soft_weights_decrease_with_suspicion(make_debate):
    votes = ["A"] * 10
    debate = make_debate(votes, [0] * 10, [votes, votes], adjacency=_chain())
    params = GuardParams(lam=2.0, eta=0.5, tau=0.5)
    p = np.linspace(0.0, 0.9, 10)
    weights = soft_weights(debate, p, params)
    assert np.all(np.diff(weights) < 0)
    assert weights.min() >= 0.0 and weights.max() <= 1.0


def test_shadow_taint_marks_echoes_of_suspicious_neighbours(make_debate):
    before = ["B"] + ["A"] * 9
    after = ["B", "B"] + ["A"] * 8
    debate = make_debate(after, [0] * 10, [before, after], adjacency=_chain(), target="B")
    params = GuardParams(tau=0.5)
    p = np.zeros(10)
    p[0] = 0.9  # agent 0 is the suspicious neighbour that agent 1 copied
    taint = shadow_taint(debate, p, params)
    assert taint[1] == 1.0
    assert taint.sum() == 1.0


def test_soft_delivery_is_deterministic_and_in_the_vote_set(make_debate):
    votes = ["A"] * 6 + ["B"] * 4
    debate = make_debate(votes, [0] * 10, [votes, votes], adjacency=_chain(), gold="A")
    params = GuardParams(lam=2.0, eta=0.5, tau=0.5)
    p = np.array([0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.9, 0.9, 0.9, 0.9])
    first, _ = soft_delivery(debate, p, params)
    second, _ = soft_delivery(debate, p, params)
    assert first == second
    assert first.answer in set(votes)
    assert first.correct is True


def test_fit_is_deterministic(debates):
    subset = [d for d in debates if d.method == "BlindGuard"][:120]
    guard_a = EpistemicGuard().fit(subset)
    guard_b = EpistemicGuard().fit(subset)
    assert guard_a.params.as_dict() == guard_b.params.as_dict()
    assert guard_a.evaluated == guard_b.evaluated


def test_guard_data_matches_single_debate_api(debates):
    subset = [d for d in debates if d.method == "PREM"][:25]
    guard = EpistemicGuard(GuardParams(a1=1.0, a2=2.0, a3=1.0, b=2.0))
    data = GuardData(subset)
    batch = data.score_hard(guard.params)
    for row, debate in enumerate(subset):
        flags = guard.flags(debate)
        assert np.array_equal(flags, batch["flags"][row])
        assert isinstance(batch["answers"][row], str)

