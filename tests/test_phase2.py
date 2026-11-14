"""Phase 2 offline proofs: Paper-1 universe, rollback, ensemble, Oracle Paradox."""

from __future__ import annotations

import numpy as np
import pytest

from gammaf_epistemic import counterfactual_audit
from gammaf_epistemic.audit_proofs import (
    ORACLE_SLICES,
    decompose_oracle_paradox,
    oracle_flags,
    oracle_slice,
)
from gammaf_epistemic.epistemic_guard import (
    EnsembleParams,
    ensemble_flags,
    ensemble_result,
    poison_links,
    rollback_delivery,
    rollback_votes,
)
from gammaf_epistemic.gammaf_clean import paper1_substitution_space


# --------------------------------------------------------------------------- #
# Task 3: the Paper 1 counterfactual universe
# --------------------------------------------------------------------------- #
def test_paper1_universe_reproduces_reference(debates):
    audit = counterfactual_audit(debates)
    paper1 = audit["universes"]["paper1_insider"]
    assert paper1["totals"]["substitutions"] == 33_025
    assert paper1["totals"]["debates_with_release_flip"] == 121
    assert paper1["totals"]["debates_with_release_flip_prior_flagged"] == 89
    assert paper1["matches_paper1_reference"] is True
    assert paper1["invariance_holds"] is True


def test_exhaustive_universe_still_reported(debates):
    audit = counterfactual_audit(debates)
    exhaustive = audit["universes"]["exhaustive_option_space"]
    assert exhaustive["totals"]["substitutions"] == 142_478
    assert exhaustive["totals"]["debates_with_release_flip"] == 470
    assert exhaustive["totals"]["release_flips"] == 2_361
    assert exhaustive["invariance_holds"] is True


def test_paper1_space_uses_only_flagged_insiders(make_debate):
    votes = ("A", "B", "C", "D", "A", "A", "A", "A", "A", "A")
    flags = (1, 0, 1, 0, 0, 0, 0, 0, 0, 0)
    debate = make_debate(
        votes,
        flags,
        [votes, votes, votes],
        insiders=(1, 2),
        adjacency=tuple(tuple(int(i != j) for j in range(10)) for i in range(10)),
    )
    space = paper1_substitution_space(debate)
    assert {sub.agent for sub in space} == {2}  # insider 1 is unflagged
    assert {sub.replacement for sub in space} == {"A", "B"}
    assert len(space) == 2


def test_paper1_space_uses_digits_for_gsm8k(make_debate):
    votes = ("1", "0", "1", "1", "1", "1", "1", "1", "1", "1")
    debate = make_debate(
        votes,
        (1, 0, 0, 0, 0, 0, 0, 0, 0, 0),
        [votes, votes],
        dataset="GSM8K",
        gold="1",
        insiders=(0,),
    )
    space = paper1_substitution_space(debate)
    assert len(space) == 1
    assert space[0].replacement == "0"


# --------------------------------------------------------------------------- #
# Task 2: rollback
# --------------------------------------------------------------------------- #
def _rollback_debate(make_debate):
    round0 = ("B", "B", "B", "A", "A", "A", "A", "A", "A", "A")
    round1 = ("B", "B", "B", "B", "A", "A", "A", "A", "A", "A")
    adjacency = [[0] * 10 for _ in range(10)]
    adjacency[0][3] = adjacency[3][0] = 1
    return make_debate(
        round1,
        (1, 1, 1, 0, 0, 0, 0, 0, 0, 0),
        [round0, round1],
        insiders=(0, 1, 2),
        adjacency=tuple(tuple(row) for row in adjacency),
    )


def test_rollback_restores_pre_contact_vote(make_debate):
    debate = _rollback_debate(make_debate)
    links = poison_links(debate, debate.flags)
    assert [(link.agent, link.insider, link.clean_vote) for link in links] == [
        (3, 0, "A")
    ]
    votes, _ = rollback_votes(debate, debate.flags)
    assert votes[3] == "A"
    delivery, _, _ = rollback_delivery(debate, debate.flags)
    assert delivery.answer == "A" and delivery.correct


def test_rollback_ignores_unflagged_source(make_debate):
    debate = _rollback_debate(make_debate)
    flags = (0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
    assert poison_links(debate, flags) == []
    votes, links = rollback_votes(debate, flags)
    assert votes == debate.votes and links == []


def test_rollback_ignores_non_adjacent_copy(make_debate):
    # Agent 3 copies agent 0's belief, but only 0 is flagged and the chain
    # neighbourhood of 3 is {2, 4}, both of which vote A.
    round0 = ("B", "A", "A", "A", "A", "A", "A", "A", "A", "A")
    round1 = ("B", "A", "A", "B", "A", "A", "A", "A", "A", "A")
    debate = make_debate(
        round1,
        (1, 0, 0, 0, 0, 0, 0, 0, 0, 0),
        [round0, round1],
        insiders=(0,),
        adjacency=tuple(
            tuple(1 if abs(i - j) == 1 else 0 for j in range(10)) for i in range(10)
        ),
    )
    assert poison_links(debate, debate.flags) == []


# --------------------------------------------------------------------------- #
# Task 2: ensemble
# --------------------------------------------------------------------------- #
def test_ensemble_rehabilitates_and_flags(make_debate):
    votes = ("A", "A", "A", "A", "A", "C", "A", "A", "A", "A")
    debate = make_debate(
        votes,
        (1, 1, 1, 0, 1, 0, 0, 0, 0, 0),
        [votes, votes],
        insiders=(0, 1, 2),
    )
    p = np.zeros(10)
    p[0] = p[1] = p[2] = 0.9
    p[5] = 0.95
    flags = ensemble_flags(
        debate,
        p,
        debate.flags,
        EnsembleParams(tau_rehab=0.4, tau_high=0.8),
        stub=np.zeros(10),
        bloc=np.zeros(10),
    )
    assert flags[4] == 0  # false positive rehabilitated
    assert flags[5] == 1  # missed insider now flagged
    assert flags.sum() <= 3


def test_ensemble_rolls_back_poisoned_neighbour(make_debate):
    debate = _rollback_debate(make_debate)
    p = np.zeros(10)
    p[:3] = 0.9
    result = ensemble_result(
        debate,
        p,
        debate.flags,
        EnsembleParams(tau_rehab=0.4, tau_high=0.8),
        stub=np.zeros(10),
        bloc=np.zeros(10),
    )
    assert result["votes"][3] == "A"
    assert result["delivery"].correct
    assert len(result["links"]) == 1


def test_ensemble_never_flags_everyone(make_debate):
    votes = ("A",) * 10
    debate = make_debate(votes, (1,) * 10, [votes, votes], insiders=(0, 1, 2))
    p = np.ones(10)
    flags = ensemble_flags(
        debate, p, debate.flags, EnsembleParams(tau_high=0.5),
        stub=np.ones(10), bloc=np.ones(10),
    )
    assert flags.sum() < 10
    assert flags.sum() <= 3


# --------------------------------------------------------------------------- #
# Task 1: Oracle Paradox
# --------------------------------------------------------------------------- #
def test_oracle_flags_exclude_insiders(make_debate):
    votes = ("A",) * 10
    debate = make_debate(votes, (0,) * 10, [votes, votes], insiders=(1, 4, 7))
    assert oracle_flags(debate) == (0, 1, 0, 0, 1, 0, 0, 1, 0, 0)


def test_oracle_slice_classification(make_debate):
    votes = ("A",) * 10
    true_adv = make_debate(votes, (0,) * 10, [votes, votes], target="B")
    self_sab = make_debate(votes, (0,) * 10, [votes, votes], target="A")
    numeric = make_debate(
        votes, (0,) * 10, [votes, votes], dataset="GSM8K", gold="1", target="0"
    )
    assert oracle_slice(true_adv) == "TRUE_ADVERSARIAL_236"
    assert oracle_slice(self_sab) == "SELF_SABOTAGED_64"
    assert oracle_slice(numeric) == "GSM8K_100"


def test_decompose_reports_all_panels(detector_debates):
    subset = [d for d in detector_debates if d.method == "XG-Guard"][:200]
    payload = decompose_oracle_paradox(subset, methods=("XG-Guard",))
    assert set(payload["by_slice"]) == set(ORACLE_SLICES)
    assert "Oracle" in payload["by_slice"]["ALL"]
    assert payload["by_slice"]["ALL"]["Oracle"]["debates"] == 200
    assert set(payload["within_stratum"]) == {"XG-Guard"}
    assert payload["xg_oracle_table"]["both"] >= 0
    assert sum(payload["discordance_types"].values()) == payload["discordance"][
        "XG-Guard"
    ]["detector_only"]
    total = sum(payload["xg_oracle_table"].values())
    assert total == 200
