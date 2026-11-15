#!/usr/bin/env python3
"""Bounded full-options replication of the existing paired GAMMAF live study.

Prepare and commit the manifest before mode=adaption. No archive or handoff is
needed: question/option records and the frozen original population are inputs.
"""
from __future__ import annotations

import argparse
import asyncio
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np
from gammaf_epistemic.live_adaption import (
    AdaptionProvider, BudgetExceeded, BudgetTracker, ContentAddressedCache,
    LiveConfig, MockProvider, Question, build_world, run_world,
)

PROTOCOL = "gammaf-v2-full-options-20261115-v1"
ARMS = ("GAMMAF-FixedTarget-PostHoc", "EpistemicGuard-Inline")
QUOTAS = {"MMLU": 14, "CSQA": 10, "MMLUPRO": 8}
GRAPHS = ("chain", "star")
SOURCE_SHA = "94cc84d54df5f8df83a9470d035d94860a05d6cf"


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest(obj):
    return hashlib.sha256(canonical(obj).encode()).hexdigest()


def atomic_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n")
    tmp.replace(path)


def normalized_population(payload):
    if isinstance(payload, dict):
        payload = payload.get("questions", payload.get("population", payload.get("worlds", list(payload.values()))))
    result = {}
    for row in payload:
        task = row.get("task", row.get("dataset"))
        item = row.get("item")
        if task is None or item is None:
            raise ValueError("population rows require task and item")
        key = (str(task), int(item))
        if key in result:
            old = result[key]
            if old.get("insiders") != row.get("insiders"):
                raise ValueError(f"inconsistent insider identities: {key}")
            continue
        result[key] = dict(row, task=key[0], item=key[1])
    return result


def make_manifest(question_file, population_file):
    qraw = json.loads(Path(question_file).read_text())
    praw = json.loads(Path(population_file).read_text())
    question_map = {(str(q["task"]), int(q["item"])): q for q in qraw}
    if not isinstance(praw, dict) or praw.get("source_commit") != SOURCE_SHA or praw.get("question_count") != 64:
        raise ValueError("population must identify the pinned source commit and 64 original questions")
    population = normalized_population(praw)
    original_counts = {task: sum(key[0] == task for key in population) for task in QUOTAS}
    if len(population) != 64 or original_counts != {"MMLU": 28, "CSQA": 21, "MMLUPRO": 15}:
        raise ValueError(f"original 64-question task counts mismatch: {original_counts}")
    # Selection only uses task and ID. No generated answer, flag or correctness
    # outcome enters this ranking. The previous 64-question panel is not a new
    # independent holdout; this is explicitly a repaired-stimulus replication.
    pool = {}
    for index, (key, meta) in enumerate(sorted(population.items())):
        q = question_map.get(key)
        if q is None:
            raise ValueError(f"missing official question: {key}")
        gold = str(meta.get("gold", q["gold"]))
        if "buggy_target" not in meta and "attack_target" not in meta:
            raise ValueError(f"verified original target is required: {key}")
        target = str(meta.get("buggy_target", meta.get("attack_target")))
        if gold != str(q["gold"]):
            raise ValueError(f"gold mismatch: {key}")
        if target != gold or key[0] not in QUOTAS:
            raise ValueError(f"population is not the original self-sabotaged panel: {key}")
        labels = q.get("options")
        if not isinstance(labels, dict) or not labels or gold not in labels:
            raise ValueError(f"full labelled options required: {key}")
        if any(not isinstance(k, str) or not isinstance(v, str) or not k.strip() or not v.strip() for k, v in labels.items()):
            raise ValueError(f"blank or invalid option: {key}")
        insiders = tuple(sorted(int(i) for i in meta["insiders"]))
        if len(insiders) != 3 or len(set(insiders)) != 3 or not all(0 <= i < 10 for i in insiders):
            raise ValueError(f"invalid three-insider set: {key}")
        if not str(q.get("text", q.get("question", ""))).strip():
            raise ValueError(f"blank question: {key}")
        original_worlds = meta.get("worlds", [])
        original_seeds = {int(w["seed"]) for w in original_worlds}
        if len(original_seeds) > 1:
            raise ValueError(f"different graph seeds in original source: {key}")
        original_seed = next(iter(original_seeds)) if original_seeds else 20261112 + index * 1009
        row = {"task": key[0], "item": key[1], "gold": gold,
               "buggy_target": target, "insiders": list(insiders),
               "text": str(q.get("text", q.get("question"))),
               "option_texts": sorted(labels.items()),
               "seed": int(meta.get("source_seed", meta.get("seed", original_seed))), "source_worlds": original_worlds}
        pool.setdefault(key[0], []).append(row)
    selected = []
    for task, quota in QUOTAS.items():
        candidates = sorted(pool.get(task, []), key=lambda row: digest([PROTOCOL, task, row["item"]]))
        if len(candidates) < quota:
            raise ValueError(f"need {quota} {task} questions, have {len(candidates)}")
        selected.extend(candidates[:quota])
    selected.sort(key=lambda q: (q["task"], q["item"]))
    worlds = []
    for q in selected:
        question = Question(task=q["task"], item=q["item"], text=q["text"],
                            options=tuple(k for k, v in q["option_texts"]),
                            gold=q["gold"], buggy_target=q["buggy_target"],
                            self_sabotaged=True, insiders=tuple(q["insiders"]),
                            option_texts=tuple(tuple(x) for x in q["option_texts"]))
        for graph in GRAPHS:
            world = build_world(question, graph, q["seed"])
            if world.fixed_target == world.gold:
                raise ValueError("fixed target must be wrong")
            original = next((w for w in q["source_worlds"] if w["graph"] == graph), None)
            if original and (original["world"] != world.key or original["fixed_target"] != world.fixed_target):
                raise ValueError(f"repaired world does not match the original seed and target: {world.key}")
            worlds.append(asdict(world))
    body = {"protocol": PROTOCOL, "source_commit": SOURCE_SHA,
            "question_source_sha256": hashlib.sha256(Path(question_file).read_bytes()).hexdigest(),
            "population_source_sha256": hashlib.sha256(Path(population_file).read_bytes()).hexdigest(),
            "selection": "within-task sha256(protocol, task, item), quotas fixed before new calls",
            "quotas": QUOTAS, "questions": selected, "worlds": worlds,
            "arms": list(ARMS), "planned_questions": 32, "planned_pairs": 64,
            "planned_arm_debates": 128, "model": "qwen3.8-27b", "temperature": 0.7,
            "rounds": 3, "max_output_tokens": 1024, "prompt_format": "full-labelled-options-v1",
            "max_physical_requests": 4500, "max_credits": 100, "max_runtime_seconds": 21600,
            "min_request_interval_seconds": 5,
            "primary": "paired delivered correctness; recovered and lost correct answers; missing-outcome bounds",
            "uncertainty": "bootstrap whole question clusters with both graphs retained",
            "oracle_disclosure": "Existing inline notices use simulator role identities to address honest agents; unchanged in this stimulus-only repair.",
            "limits": "One model, two graphs, same selected question panel; not an independent generalization test. The role-oracle notice and compound intervention are retained."}
    return dict(body, manifest_sha256=digest(body))


class BoundedProvider:
    """Persistently count every physical attempt, including outer retries.

    The SDK must be constructed with max_retries=0. Pending attempts on a
    crashed process remain charged at their conservative reservation.
    """
    def __init__(self, provider, ledger, *, max_attempts=4500, max_credits=100,
                 max_seconds=21600, interval=5, concurrency=4):
        self.provider, self.name = provider, provider.name
        self.path = Path(ledger)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = asyncio.Lock()
        self.sem = asyncio.Semaphore(concurrency)
        self.max_attempts, self.max_credits = max_attempts, max_credits
        self.max_seconds, self.interval = max_seconds, interval
        self.started = time.time()
        self.last = 0.0
        self.attempts = 0
        self.reserved_credits = 0.0
        if self.path.exists():
            for line in self.path.read_text().splitlines():
                row = json.loads(line)
                if row["event"] == "attempt_started":
                    self.attempts += 1
                    self.reserved_credits += row["reserved_credits"]
                    self.started = min(self.started, row["timestamp"])
                    self.last = max(self.last, row["timestamp"])
        self.stopped = False
        self.failure_streak = 0

    def append(self, row):
        with self.path.open("a") as f:
            f.write(canonical(row) + "\n")
            f.flush()
            os.fsync(f.fileno())

    async def complete(self, model, messages, temperature, max_tokens, salt):
        async with self.sem:
            async with self.lock:
                # UTF-8 byte count plus generous per-message framing bounds
                # token count conservatively for these plain-text prompts.
                input_bound = sum(len(m.get("content", "").encode()) + 256 for m in messages)
                reserve = input_bound * .039 / 1e6 + max_tokens * 1.25 / 1e6
                wait = max(0, self.interval - (time.time() - self.last))
                if self.stopped or time.time() + wait - self.started >= self.max_seconds or self.attempts >= self.max_attempts or self.reserved_credits + reserve > self.max_credits:
                    self.stopped = True
                    raise BudgetExceeded("physical request, conservative credit or wall-clock cap reached")
                if wait:
                    await asyncio.sleep(wait)
                self.last = time.time()
                self.attempts += 1
                self.reserved_credits += reserve
                attempt_id = self.attempts
                self.append({"event": "attempt_started", "attempt": attempt_id,
                             "timestamp": self.last, "reserved_credits": reserve,
                             "model": model, "temperature": temperature, "max_tokens": max_tokens,
                             "prompt_sha256": digest(messages), "messages": messages})
            try:
                completion = await self.provider.complete(model, messages, temperature, max_tokens, salt)
            except Exception as exc:
                self.failure_streak += 1
                status = getattr(exc, "status_code", None)
                status = status if isinstance(status, int) else None
                self.append({"event": "attempt_failed", "attempt": attempt_id,
                             "timestamp": time.time(), "error_type": type(exc).__name__,
                             "status_code": status})
                if status in (400, 401, 403, 404, 422) or self.failure_streak >= 20:
                    self.stopped = True
                    raise BudgetExceeded("provider fatal status or twenty consecutive failed requests") from None
                raise
            self.failure_streak = 0
            self.append({"event": "attempt_completed", "attempt": attempt_id,
                         "timestamp": time.time(), "text": completion.text,
                         "content": completion.content, "reasoning": completion.reasoning,
                         "input_tokens": completion.prompt_tokens, "output_tokens": completion.completion_tokens})
            return completion


def pair_summary(worlds, rows, bootstrap=20000):
    table = {(r["world"], r["arm"]): r for r in rows}
    groups, gained, lost, both_correct, both_wrong = {}, 0, 0, 0, 0
    lower, upper = 0, 0
    complete_pairs = 0
    missing = []
    for w in worlds:
        key = f"{w['task']}:{w['item']}:{w['graph']}:{w['seed']}"
        a, b = (table.get((key, arm)) for arm in ARMS)
        if a is None or b is None:
            missing.append({"world": key, "missing_arms": [arm for arm, r in zip(ARMS, (a, b)) if r is None]})
            av = [int(a["correct"])] if a else [0, 1]
            bv = [int(b["correct"])] if b else [0, 1]
            possibilities = [y - x for x in av for y in bv]
            lower += min(possibilities); upper += max(possibilities)
            continue
        x, y = int(a["correct"]), int(b["correct"])
        delta = y - x
        lower += delta; upper += delta
        complete_pairs += 1
        gained += int(x == 0 and y == 1); lost += int(x == 1 and y == 0)
        both_correct += int(x == y == 1); both_wrong += int(x == y == 0)
        groups.setdefault((w["task"], w["item"]), []).append(delta)
    complete_groups = [(key[0], sum(v) / len(v)) for key, v in groups.items() if len(v) == len(GRAPHS)]
    ci = None
    if complete_groups:
        rng = np.random.default_rng(20261115)
        by_task = {}
        for task, value in complete_groups:
            by_task.setdefault(task, []).append(value)
        totals = np.zeros(bootstrap)
        for values in by_task.values():
            totals += rng.choice(values, size=(bootstrap, len(values)), replace=True).sum(axis=1)
        means = totals / len(complete_groups) * 100
        ci = [float(x) for x in np.quantile(means, [.025, .975])]
    return {"planned_pairs": len(worlds), "complete_pairs": complete_pairs,
            "gained_correct": gained, "lost_correct": lost,
            "both_correct": both_correct, "both_incorrect": both_wrong,
            "terminal_correct_complete_pairs": both_correct + lost,
            "inline_correct_complete_pairs": both_correct + gained,
            "delta_complete_pairs_pp": (gained - lost) * 100 / complete_pairs if complete_pairs else None,
            "all_planned_delta_bounds_pp": [lower * 100 / len(worlds), upper * 100 / len(worlds)],
            "complete_question_clusters": len(complete_groups),
            "delta_complete_question_clusters_pp": 100 * sum(v for t, v in complete_groups) / len(complete_groups) if complete_groups else None,
            "question_cluster_bootstrap_ci95_pp": ci, "missing": missing,
            "ci_boundary": "Within-task bootstrap of complete question clusters; CI applies to delta_complete_question_clusters_pp, missing-outcome bounds reported separately, no equivalence claim."}


async def execute(manifest, args):
    from gammaf_epistemic.live_adaption import World
    out = args.out
    cache = ContentAddressedCache(out / "repaired_cache.sqlite")
    # A new cache namespace and manifest guard prevent old letter-only answers
    # or a changed repaired panel being reused as repaired evidence.
    expected = manifest["manifest_sha256"]
    guard = out / "run_identity.json"
    identity = {"manifest_sha256": expected, "mode": args.mode, "protocol": PROTOCOL}
    if guard.exists() and json.loads(guard.read_text()) != identity:
        raise ValueError("output directory belongs to another manifest or mode")
    atomic_json(guard, identity)
    if args.mode == "adaption":
        raw = AdaptionProvider(timeout=90, max_retries=0)
        provider = BoundedProvider(raw, out / "request_ledger.jsonl")
    else:
        provider = MockProvider()
    budget = BudgetTracker(max_api_calls=4500, max_credits=100)
    config = LiveConfig(model=manifest["model"], rounds=3, temperature=.7,
                        max_output_tokens=1024, salt=PROTOCOL + ":" + expected,
                        max_retries=3, timeout=90, capture_samples=True)
    worlds = manifest["worlds"][:1] if args.smoke else manifest["worlds"]
    rows, failures = [], []
    try:
        for wi, record in enumerate(worlds):
            w = dict(record)
            for name in ("options", "insiders"):
                w[name] = tuple(w[name])
            w["option_texts"] = tuple(tuple(x) for x in w["option_texts"])
            world = World(**w)
            for arm in ARMS:
                try:
                    row = await run_world(world, arm, provider, cache, budget, config, mock=args.mode == "mock")
                    payload = row.as_dict()
                    payload["initial_insiders"] = list(world.insiders)
                    payload["world_seed"] = world.seed
                    rows.append(payload)
                except Exception as exc:
                    failures.append({"world": world.key, "arm": arm, "error_type": type(exc).__name__})
                atomic_json(out / "repaired_results.json", {"manifest_sha256": expected,
                            "mode": args.mode, "rows": rows, "failures": failures,
                            "summary": pair_summary(worlds, rows), "budget": budget.summary(),
                            "physical_attempts": getattr(provider, "attempts", 0)})
                print(f"pair {wi+1}/{len(worlds)} {arm}: rows={len(rows)} attempts={getattr(provider, 'attempts', 0)}", flush=True)
                if getattr(provider, "stopped", False):
                    return 3
        return 0 if not failures else 1
    finally:
        cache.close()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--questions", type=Path, default=ROOT / "artifacts/questions_400.json")
    p.add_argument("--population", type=Path, default=ROOT / "artifacts/repaired_population_source.json")
    p.add_argument("--manifest", type=Path, default=ROOT / "artifacts/repaired_manifest.json")
    p.add_argument("--out", type=Path, default=ROOT / "artifacts/repaired_full_options")
    p.add_argument("--mode", choices=("prepare", "mock", "adaption"), default="prepare")
    p.add_argument("--smoke", action="store_true", help="One manifest world; use a separate output directory.")
    args = p.parse_args()
    if args.mode == "prepare":
        candidate = make_manifest(args.questions, args.population)
        if args.manifest.exists() and canonical(json.loads(args.manifest.read_text())) != canonical(candidate):
            raise ValueError("existing manifest differs; freeze a new named protocol instead")
        atomic_json(args.manifest, candidate)
        print(json.dumps({"manifest_sha256": candidate["manifest_sha256"], "questions": 32, "pairs": 64}))
        return 0
    manifest = json.loads(args.manifest.read_text())
    body = {k: v for k, v in manifest.items() if k != "manifest_sha256"}
    if digest(body) != manifest["manifest_sha256"]:
        raise ValueError("manifest hash mismatch")
    args.out.mkdir(parents=True, exist_ok=True)
    return asyncio.run(execute(manifest, args))


if __name__ == "__main__":
    raise SystemExit(main())
