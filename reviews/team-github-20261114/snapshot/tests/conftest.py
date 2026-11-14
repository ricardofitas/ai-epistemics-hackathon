"""Shared fixtures: one archive load per session, plus synthetic debates."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from gammaf_epistemic import load_debates  # noqa: E402
from gammaf_epistemic.data import Debate, Round  # noqa: E402


@pytest.fixture(scope="session")
def debates():
    return load_debates()


@pytest.fixture(scope="session")
def detector_debates(debates):
    return [d for d in debates if not d.is_control]


@pytest.fixture
def make_debate():
    def factory(
        votes,
        flags,
        trajectories,
        *,
        gold="A",
        dataset="MMLU",
        graph="chain",
        adjacency=None,
        insiders=(),
        target="B",
        item=0,
        method="TEST",
        round_flags=None,
    ):
        per_round = round_flags or [flags] * len(trajectories)
        rounds = tuple(
            Round(
                index=index,
                votes=tuple(v),
                flags=tuple(per_round[index]),
            )
            for index, v in enumerate(trajectories)
        )
        if adjacency is None:
            adjacency = tuple(
                tuple(0 if i == j else 1 for j in range(len(votes)))
                for i in range(len(votes))
            )
        return Debate(
            dataset=dataset,
            method=method,
            item=item,
            graph=graph,
            gold=gold,
            votes=tuple(votes),
            flags=tuple(flags),
            executed_rounds=len(rounds),
            published=0,
            actual=0,
            all_answer="",
            delivered="",
            rounds=rounds,
            adjacency=tuple(tuple(int(v) for v in row) for row in adjacency),
            insiders=tuple(insiders),
            attack_target=target,
        )

    return factory

