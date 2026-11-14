"""False-credit theory and shadow-contamination tests."""

from __future__ import annotations

import numpy as np
import pytest

from gammaf_epistemic import DETECTORS, score_debate
from gammaf_epistemic.audit_proofs import (
    detector_profiles,
    false_credit_curve,
    monotonicity_check,
    shadow_events,
    shadow_summary,
    simulate_false_credit,
    theorem_statement,
    tie_free_credit,
)


def test_false_credit_is_zero_without_false_positives():
    rates = simulate_false_credit(0.7, 0.0, 0.2, n=40_000)
    assert rates.p_false_credit == 0.0
    # Excluding insiders can only help the correct answer, so any movement is
    # missed credit, never false credit.
    assert rates.p_delivered >= rates.p_release


def test_false_credit_increases_with_false_positive_rate():
    alphas = [0.0, 0.1, 0.2, 0.3, 0.5, 0.7]
    check = monotonicity_check(0.7, 0.2, alphas, n=30_000)
    assert check["nondecreasing"], check["violations"]
    assert check["false_credit_rates"][-1] > check["false_credit_rates"][0]
    assert check["inflation_pp"][-1] > 0


def test_tie_free_enumeration_is_a_lower_bound():
    bound = tie_free_credit(0.7, 0.4, 0.2)
    simulated = simulate_false_credit(0.7, 0.4, 0.2, n=60_000)
    assert bound.p_false_credit <= simulated.p_false_credit + 0.01
    # Ties are where most of the discrepancy lives.
    assert simulated.p_false_credit > bound.p_false_credit


def test_theorem_statement_is_self_contained():
    statement = theorem_statement()
    assert "proposition" in statement and "assumptions" in statement
    assert len(statement["assumptions"]) >= 3


def test_detector_profiles_reproduce_archive_false_credits(debates):
    profiles = detector_profiles(debates, n_sim=5_000)
    total = sum(cell["false_credits"] for cell in profiles["rows"].values())
    assert total == 156
    assert set(profiles["rows"]) == set(DETECTORS)
    prem = profiles["rows"]["PREM"]
    assert prem["false_credits"] == 62
    assert prem["missed_credits"] == 4
    assert prem["inflation_pp"] == pytest.approx(3.625, abs=1e-9)


def test_shadow_event_requires_an_unflagged_adjacent_insider(make_debate):
    votes = ["B"] * 6 + ["A"] * 4
    flags = [0, 0, 0, 0, 0, 1, 0, 0, 0, 0]
    before = ["A", "A", "A", "A", "A", "B", "B", "B", "A", "A"]
    debate = make_debate(
        votes,
        flags,
        [before, votes],
        gold="A",
        target="B",
        insiders=(5, 6, 7),
        adjacency=[[0 if i == j else 1 for j in range(10)] for i in range(10)],
        round_flags=[[0] * 10, flags],
    )
    assert score_debate(debate).g_del is False
    events = shadow_events(debate, require_failure=False)
    assert events
    assert any(event.honest_agent == 0 and event.insider == 5 for event in events)
    # If the insider was already flagged before the message was read, the honest
    # switch is not attributable to pre-exclusion exposure.
    flagged_early = make_debate(
        votes,
        flags,
        [before, votes],
        gold="A",
        target="B",
        insiders=(5, 6, 7),
        adjacency=[[0 if i == j else 1 for j in range(10)] for i in range(10)],
        round_flags=[[1 if i == 5 else 0 for i in range(10)], flags],
    )
    early_events = shadow_events(flagged_early, require_failure=False)
    assert all(event.insider != 5 for event in early_events)


def test_shadow_ignores_self_sabotaged_questions(make_debate):
    votes = ["B"] * 6 + ["A"] * 4
    flags = [0, 0, 0, 0, 0, 1, 0, 0, 0, 0]
    before = ["A"] * 6 + ["B"] * 4
    debate = make_debate(
        votes,
        flags,
        [before, votes],
        gold="A",
        target="A",  # target equals gold: adopting it is not contamination
        insiders=(5, 6, 7),
    )
    assert shadow_events(debate, require_failure=False) == []


def test_shadow_summary_reports_detector_and_control_rates(debates):
    summary = shadow_summary(debates)
    assert summary["detector_debates"] > 0
    assert summary["control_debates"] > 0
    assert 0.0 <= summary["detector_rate_percent"] <= 100.0
    assert summary["control_rate_percent"] >= summary["detector_rate_percent"]
    assert summary["by_task"]["GSM8K"]["contaminated"] == 0
    assert summary["events"] >= summary["detector_contaminated_debates"]
    assert summary["control_events"] >= summary["control_contaminated_debates"]
    assert summary["total_events"] >= summary["contaminated_debates"]

