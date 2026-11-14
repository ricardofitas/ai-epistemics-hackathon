"""Archive access for GAMMAF experiment 1 (upstream commit ``53be3249``).

The handoff bundle under ``swarmlab-gammaf/gammaf_handoff`` contains

* ``gamma_debates.jsonl.gz`` - 11,200 terminal decisions (9,600 detector
  debates + 1,600 disabled-detector controls), one JSON object per debate.
* ``_source/experiments-Information-Sciences/experiment1/results/
  summary-exp1-scores/<TASK>/<METHOD>.json`` - the pinned upstream records,
  including the *executed* per-round grid, the adjacency matrix, the true
  insider indices, the padding markers and the effective RNG seeds.

This module turns both layers into a single immutable :class:`Debate` view.
Nothing is recomputed from a model: every field is read from the archive or
derived deterministically from it.

Schema (terminal debate, ``gamma_debates.jsonl.gz``)::

    dataset:str  method:str  item:int  graph:str  executed_rounds:int
    gold:str  votes:[str]*10  flagged:[0|1]*10  all_answer:str
    delivered:str  published:0|1  actual:0|1
    disagreement:0|1  false_credit:0|1  missed_credit:0|1
    perturbable:0|1  alerts:int

Schema (upstream round record, fields used by this package)::

    round:int  padded:bool  included:bool  loader_index:int  topology:str
    agent_answers:[str]*10  flags:[0|1]*10  initial_topology:[[int]]*10
    malicious_agent_indexes:[int]*3  metrics:{ADR:float,...}
    effective_seeds:{answer_seed_effective:int, ...}
"""

from __future__ import annotations

import gzip
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Iterator, Mapping, Sequence

import numpy as np

DETECTORS: tuple[str, ...] = (
    "BlindGuard",
    "CASPIAN",
    "DOMINANT",
    "PREM",
    "TAM",
    "XG-Guard",
)
CONTROL = "no_defense_baseline"
METHODS: tuple[str, ...] = DETECTORS + (CONTROL,)

TASKS: tuple[str, ...] = ("MMLU", "MMLUPRO", "CSQA", "GSM8K")
TASK_LABELS: dict[str, str] = {
    "MMLU": "MMLU",
    "MMLUPRO": "MMLU-Pro",
    "CSQA": "CSQA",
    "GSM8K": "GSM8K",
}
TOPOLOGIES: tuple[str, ...] = ("chain", "random", "star", "tree")

#: Canonical option space A(q) per task. ``None`` means a free-form numeric task.
OPTION_SPACE: dict[str, str | None] = {
    "MMLU": "ABCD",
    "MMLUPRO": "ABCDEFGHIJ",
    "CSQA": "ABCDE",
    "GSM8K": None,
}

N_AGENTS = 10
N_INSIDERS = 3


# --------------------------------------------------------------------------- #
# Records
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Round:
    """One executed (or padded) debate round."""

    index: int
    votes: tuple[str, ...]
    flags: tuple[int, ...]
    adr_percent: float = 0.0
    padded: bool = False


@dataclass(frozen=True)
class Debate:
    """A single archived method-debate (task x detector x question x topology)."""

    dataset: str
    method: str
    item: int
    graph: str
    gold: str
    votes: tuple[str, ...]
    flags: tuple[int, ...]
    executed_rounds: int
    published: int
    actual: int
    all_answer: str
    delivered: str
    rounds: tuple[Round, ...] = ()
    padded_rounds: tuple[Round, ...] = ()
    adjacency: tuple[tuple[int, ...], ...] = ()
    insiders: tuple[int, ...] = ()
    attack_target: str | None = None
    seed: int | None = None

    # -- identity ---------------------------------------------------------- #
    @property
    def question_key(self) -> tuple[str, int]:
        return (self.dataset, self.item)

    @property
    def key(self) -> tuple[str, str, int, str]:
        return (self.dataset, self.method, self.item, self.graph)

    @property
    def is_control(self) -> bool:
        return self.method == CONTROL

    @property
    def n_agents(self) -> int:
        return len(self.votes)

    # -- flags / franchises ------------------------------------------------ #
    @property
    def eligible(self) -> tuple[int, ...]:
        return tuple(i for i, f in enumerate(self.flags) if not f)

    @property
    def excluded(self) -> tuple[int, ...]:
        return tuple(i for i, f in enumerate(self.flags) if f)

    @property
    def is_valid_attack_target(self) -> bool:
        """False only for the 64 canonical MCQ questions pushed onto the gold answer."""
        return self.attack_target is None or self.attack_target != self.gold

    @property
    def option_space(self) -> str | None:
        return OPTION_SPACE[self.dataset]

    @property
    def has_trajectory(self) -> bool:
        return len(self.rounds) >= 1

    def neighbors(self, agent: int) -> tuple[int, ...]:
        if not self.adjacency:
            return tuple(j for j in range(self.n_agents) if j != agent)
        row = self.adjacency[agent]
        return tuple(j for j, v in enumerate(row) if v and j != agent)

    def flagged_before(self, agent: int, round_pos: int) -> bool:
        """True when ``agent`` was already flagged in an earlier executed round."""
        return any(r.flags[agent] for r in self.rounds[:round_pos])


@dataclass(frozen=True)
class Slices:
    """Question-level stratification induced by the released attack sampler."""

    all_questions: frozenset[tuple[str, int]]
    true_adversarial: frozenset[tuple[str, int]]
    self_sabotaged: frozenset[tuple[str, int]]

    def names(self) -> dict[str, frozenset[tuple[str, int]]]:
        return {
            "ALL_400": self.all_questions,
            "TRUE_ADVERSARIAL_236": self.true_adversarial,
            "SELF_SABOTAGED_64": self.self_sabotaged,
        }


# --------------------------------------------------------------------------- #
# Archive discovery
# --------------------------------------------------------------------------- #
def _resolve_handoff(explicit: str | Path | None = None) -> Path:
    candidates: list[Path] = []
    if explicit is not None:
        candidates.append(Path(explicit))
    env = os.environ.get("GAMMAF_HANDOFF")
    if env:
        candidates.append(Path(env))
    root = Path(__file__).resolve().parents[1]
    cwd = Path.cwd()
    for base in (cwd, root, root.parent, *cwd.parents):
        candidates.append(base / "swarmlab-gammaf" / "gammaf_handoff")
        candidates.append(base / "gammaf_handoff")
    for candidate in candidates:
        if (candidate / "gamma_debates.jsonl.gz").is_file():
            return candidate.resolve()
    for match in root.rglob("gamma_debates.jsonl.gz"):
        return match.parent.resolve()
    raise FileNotFoundError(
        "gamma_debates.jsonl.gz not found; pass --handoff or set GAMMAF_HANDOFF"
    )


def handoff_dir(explicit: str | Path | None = None) -> Path:
    return _resolve_handoff(explicit)


def _raw_path(handoff: Path, dataset: str, method: str) -> Path:
    return (
        handoff
        / "_source"
        / "experiments-Information-Sciences"
        / "experiment1"
        / "results"
        / "summary-exp1-scores"
        / dataset
        / f"{method}.json"
    )


# --------------------------------------------------------------------------- #
# Attack target: the released (buggy) sampler, replayed from its recorded seed
# --------------------------------------------------------------------------- #
def released_target_from_seed(seed: int) -> str:
    """Replay the released target generator.

    Upstream reads::

        answer_rng = np.random.default_rng(self.answer_seed + 100000 + index)
        wrong_answer_idx = int(answer_rng.choice([i for i in range(0, 4)
                                                  if i != ground_truth]))
        mal_answer = chr(wrong_answer_idx + 65)

    ``ground_truth`` is a letter, so ``i != ground_truth`` is always true
    (integer index compared with a string): the gold answer is never excluded
    and only options ``A``-``D`` are ever drawn.  This function reproduces that
    draw exactly, which is what makes the 64/300 stratification auditable.
    """
    rng = np.random.default_rng(int(seed))
    return chr(int(rng.choice([0, 1, 2, 3])) + 65)


# --------------------------------------------------------------------------- #
# Loading
# --------------------------------------------------------------------------- #
def _round_from_item(item: Mapping[str, Any]) -> Round:
    metrics = item.get("metrics") or {}
    return Round(
        index=int(item["round"]),
        votes=tuple(str(a) for a in item["agent_answers"]),
        flags=tuple(int(f) for f in item["flags"]),
        adr_percent=float(metrics.get("ADR", 0.0) or 0.0),
        padded=bool(item.get("padded", False)),
    )


def _read_terminal(path: Path) -> list[dict[str, Any]]:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def _read_raw_rounds(path: Path) -> dict[tuple[int, str], dict[str, Any]]:
    """Compact per-debate round grid, keyed by (loader_index, topology)."""
    if not path.is_file():
        return {}
    with open(path, "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    grouped: dict[tuple[int, str], dict[str, Any]] = {}
    for item in payload.get("items", []):
        if not item.get("included", False):
            continue
        key = (int(item["loader_index"]), str(item["topology"]))
        entry = grouped.setdefault(
            key,
            {
                "executed": [],
                "padded": [],
                "adjacency": None,
                "insiders": tuple(int(i) for i in item.get("malicious_agent_indexes", [])),
                "seed": None,
            },
        )
        if item.get("initial_topology") and entry["adjacency"] is None:
            entry["adjacency"] = tuple(
                tuple(int(v) for v in row) for row in item["initial_topology"]
            )
        if item.get("effective_seeds") and entry["seed"] is None:
            entry["seed"] = int(
                item["effective_seeds"].get("answer_seed_effective")
            ) if item["effective_seeds"].get("answer_seed_effective") is not None else None
        round_obj = _round_from_item(item)
        (entry["padded"] if round_obj.padded else entry["executed"]).append(round_obj)
    for entry in grouped.values():
        entry["executed"].sort(key=lambda r: r.index)
        entry["padded"].sort(key=lambda r: r.index)
    return grouped


def load_debates(
    handoff: str | Path | None = None,
    *,
    with_trajectories: bool = True,
    verbose: bool = False,
) -> list[Debate]:
    """Load all 11,200 archived debates with their executed trajectories."""
    root = handoff_dir(handoff)
    terminal = _read_terminal(root / "gamma_debates.jsonl.gz")
    raw_cache: dict[tuple[str, str], dict[tuple[int, str], dict[str, Any]]] = {}
    if with_trajectories:
        for dataset in TASKS:
            for method in METHODS:
                raw_cache[(dataset, method)] = _read_raw_rounds(
                    _raw_path(root, dataset, method)
                )
        if verbose:
            found = sum(1 for grid in raw_cache.values() if grid)
            print(f"[data] raw round grids found: {found}/{len(raw_cache)}")
    debates: list[Debate] = []
    for record in terminal:
        dataset = str(record["dataset"])
        method = str(record["method"])
        item = int(record["item"])
        graph = str(record["graph"])
        entry = raw_cache.get((dataset, method), {}).get((item, graph))
        votes = tuple(str(v) for v in record["votes"])
        flags = tuple(int(f) for f in record["flagged"])
        rounds: tuple[Round, ...] = ()
        padded: tuple[Round, ...] = ()
        adjacency: tuple[tuple[int, ...], ...] = ()
        insiders: tuple[int, ...] = ()
        seed: int | None = None
        if entry is not None and entry["executed"]:
            rounds = tuple(entry["executed"])
            padded = tuple(entry["padded"])
            adjacency = entry["adjacency"] or ()
            insiders = entry["insiders"]
            seed = entry["seed"]
            last = rounds[-1]
            if last.votes != votes or last.flags != flags:
                raise ValueError(f"terminal record disagrees with trajectory at {record}")
        elif with_trajectories:
            raise ValueError(f"missing trajectory for {record['dataset']}/{method}/{item}/{graph}")
        target = released_target_from_seed(seed) if seed is not None else None
        debates.append(
            Debate(
                dataset=dataset,
                method=method,
                item=item,
                graph=graph,
                gold=str(record["gold"]),
                votes=votes,
                flags=flags,
                executed_rounds=int(record["executed_rounds"]),
                published=int(record["published"]),
                actual=int(record["actual"]),
                all_answer=str(record["all_answer"]),
                delivered=str(record["delivered"]),
                rounds=rounds,
                padded_rounds=padded,
                adjacency=adjacency,
                insiders=insiders,
                attack_target=target,
                seed=seed,
            )
        )
    if len(debates) != 11200:
        raise ValueError(f"expected 11,200 debates, found {len(debates)}")
    return debates


# --------------------------------------------------------------------------- #
# Stratification
# --------------------------------------------------------------------------- #
def slices_of(debates: Sequence[Debate]) -> Slices:
    all_q: set[tuple[str, int]] = set()
    adversarial: set[tuple[str, int]] = set()
    sabotaged: set[tuple[str, int]] = set()
    for debate in debates:
        all_q.add(debate.question_key)
        if debate.is_valid_attack_target:
            adversarial.add(debate.question_key)
        else:
            sabotaged.add(debate.question_key)
    return Slices(
        all_questions=frozenset(all_q),
        true_adversarial=frozenset(adversarial),
        self_sabotaged=frozenset(sabotaged),
    )


def in_slice(debate: Debate, name: str, slices: Slices) -> bool:
    if name == "ALL_400":
        return True
    if name == "TRUE_ADVERSARIAL_236":
        return debate.question_key in slices.true_adversarial
    if name == "SELF_SABOTAGED_64":
        return debate.question_key in slices.self_sabotaged
    raise KeyError(name)


def slice_counts(debates: Sequence[Debate]) -> dict[str, dict[str, int]]:
    slices = slices_of(debates)
    result: dict[str, dict[str, int]] = {}
    for name, questions in slices.names().items():
        members = [d for d in debates if d.question_key in questions]
        result[name] = {
            "questions": len(questions),
            "detector_debates": sum(1 for d in members if not d.is_control),
            "control_debates": sum(1 for d in members if d.is_control),
        }
    return result


def valid_target_questions(debates: Sequence[Debate]) -> set[tuple[str, int]]:
    return set(slices_of(debates).true_adversarial)


# --------------------------------------------------------------------------- #
# Schema dump (Step 1 of the brief)
# --------------------------------------------------------------------------- #
def _describe(value: Any) -> str:
    if isinstance(value, list):
        inner = _describe(value[0]) if value else "empty"
        return f"list[{len(value)}] of {inner}"
    if isinstance(value, dict):
        return "object{" + ", ".join(sorted(value)) + "}"
    return type(value).__name__


def schema_report(handoff: str | Path | None = None) -> str:
    """Exact schema of the archived debate logs, as found on disk."""
    root = handoff_dir(handoff)
    terminal_path = root / "gamma_debates.jsonl.gz"
    records = _read_terminal(terminal_path)
    raw_path = _raw_path(root, "MMLU", "BlindGuard")
    raw_items: list[dict[str, Any]] = []
    if raw_path.is_file():
        with open(raw_path, "r", encoding="utf-8") as handle:
            raw_items = json.load(handle).get("items", [])[:1]
    lines: list[str] = []
    lines.append(f"handoff: {root}")
    lines.append(f"terminal file: {terminal_path.name}  records={len(records)}")
    lines.append("terminal record fields:")
    sample = records[0]
    for key in sorted(sample):
        lines.append(f"  {key:18s} {_describe(sample[key])}")
    lines.append("")
    if raw_items:
        lines.append(f"upstream round record: {raw_path.relative_to(root)}")
        lines.append("round record fields:")
        for key in sorted(raw_items[0]):
            lines.append(f"  {key:18s} {_describe(raw_items[0][key])}")
        lines.append("")
    lines.append("derived Debate fields:")
    lines.append(
        "  dataset, method, item, graph, gold, votes[10], flags[10], executed_rounds,"
        " published, actual, all_answer, delivered, rounds[], padded_rounds[],"
        " adjacency[10][10], insiders[], attack_target, seed"
    )
    return "\n".join(lines)


def main() -> None:  # pragma: no cover - CLI helper
    print(schema_report())


if __name__ == "__main__":  # pragma: no cover
    main()

