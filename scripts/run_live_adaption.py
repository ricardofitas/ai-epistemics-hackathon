#!/usr/bin/env python
"""Run the live Adaption inline suite and emit tables, a figure and JSON.

Examples::

    python scripts/run_live_adaption.py --tier smoke --mode mock
    python scripts/run_live_adaption.py --tier sabotage64 --mode mock
    export ADAPTION_API_KEY=...
    python scripts/run_live_adaption.py --tier sabotage64 --mode adaption
    python scripts/run_live_adaption.py --tier full400 --mode adaption

Tiers (base worlds x 4 paired arms)::

    sanity      1 question x 1 topology     = 1 world   / 4 arm-debates
    smoke       4 questions x 4 topologies  = 16 worlds  / 64 arm-debates
    sabotage64  64 self-sabotaged x 4       = 256 worlds / 1,024 arm-debates
    full400     400 questions x 4           = 1,600 worlds / 6,400 arm-debates
    multmodel   80 stratified x 4 x 3 models = 960 worlds / 3,840 arm-debates

Outputs: ``Table_Live_Adaption.tex``, ``fig_live_inline_vs_posthoc.png`` and
``live_results.json``.  Mock mode is a harness check, not a model result.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from gammaf_epistemic.live_adaption import (  # noqa: E402
    ARMS,
    AdaptionProvider,
    BudgetTracker,
    ContentAddressedCache,
    LiveConfig,
    MockProvider,
    load_questions,
    paired_bootstrap,
    run_suite,
    select_worlds,
    summarize,
)

MULTI_MODELS = ("qwen3.8-27b", "deepseek-v4-flash", "gemma-4-26b-a4b-it")
TIER_ALIASES = {"multMODEL": "multmodel", "multmodel": "multmodel"}


class Throttled:
    """Provider wrapper enforcing the global ``--concurrency`` limit."""

    def __init__(self, provider, limit: int):
        self.provider = provider
        self.name = getattr(provider, "name", "provider")
        self.semaphore = asyncio.Semaphore(max(limit, 1))

    async def complete(self, *args, **kwargs):
        async with self.semaphore:
            return await self.provider.complete(*args, **kwargs)


def print_table(title: str, headers: Sequence[str], rows: Sequence[Sequence]) -> None:
    print(f"\n{title}")
    width = [max(len(str(h)), *(len(f"{row[i]}") for row in rows)) if rows else len(str(h))
             for i, h in enumerate(headers)]
    print("  ".join(str(h).ljust(w) for h, w in zip(headers, width)))
    print("  ".join("-" * w for w in width))
    for row in rows:
        print("  ".join(f"{value}".ljust(w) for value, w in zip(row, width)))


def latex_table(path: Path, caption: str, label: str, headers, rows, note: str) -> None:
    lines = [
        r"\begin{table}[htbp]",
        r"\centering",
        r"\small",
        rf"\caption{{{caption}}}",
        rf"\label{{{label}}}",
        rf"\begin{{tabular}}{{{'l' * 2 + 'r' * (len(headers) - 2)}}}",
        r"\toprule",
        " & ".join(headers) + r" \\",
        r"\midrule",
    ]
    for row in rows:
        lines.append(" & ".join(str(value) for value in row) + r" \\")
    lines.extend([r"\bottomrule", r"\end{tabular}", rf"\par\smallskip\footnotesize {note}", r"\end{table}"])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _mode(args) -> str | None:
    if args.mode == "mock":
        return "mock"
    if args.mode == "adaption":
        return "adaption"
    has_key = bool(os.environ.get("ADAPTION_API_KEY") or os.environ.get("OPENAI_API_KEY"))
    try:
        import adaption  # noqa: F401
    except ImportError:
        return None
    return "adaption" if has_key else None


def _print_missing_credentials() -> None:
    print("No live Adaption credentials/SDK found in this shell.\n")
    print("PowerShell (this machine):")
    print("  $env:ADAPTION_API_KEY='<your-key>'; $env:SWARMLAB_PROVIDER='adaption'")
    print("bash / Git Bash:")
    print("  export ADAPTION_API_KEY='<your-key>' SWARMLAB_PROVIDER='adaption'")
    print("then, if needed:  pip install adaption")
    print("\nLaunch commands:")
    print("  python scripts/run_live_adaption.py --tier sabotage64 --mode adaption")
    print("  python scripts/run_live_adaption.py --tier full400 --mode adaption")
    print("\nAdd --max-credits N (or --max-api-calls N) to stop inside a budget; "
          "completed debates are checkpointed and resume for free.")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tier", default="smoke",
                        choices=("sanity", "smoke", "sabotage64", "full400",
                                 "multmodel", "multMODEL"))
    parser.add_argument("--mode", default="auto", choices=("auto", "mock", "adaption"))
    parser.add_argument("--model", action="append", default=None)
    parser.add_argument("--out", type=Path, default=ROOT / "artifacts")
    parser.add_argument("--cache", type=Path, default=ROOT / "artifacts" / "live_cache.sqlite")
    parser.add_argument("--handoff", type=Path, default=None)
    parser.add_argument("--questions-json", type=Path, default=None)
    parser.add_argument("--download-questions", action="store_true")
    parser.add_argument("--allow-synthetic-questions", action="store_true")
    parser.add_argument("--rounds", type=int, default=3)
    parser.add_argument("--max-tokens", type=int, default=1024)
    parser.add_argument("--purge-empty-cache", action="store_true")
    parser.add_argument("--concurrency", type=int, default=8)
    parser.add_argument("--max-api-calls", type=int, default=None)
    parser.add_argument("--max-credits", type=float, default=None)
    parser.add_argument("--inline-tau", type=float, default=0.65)
    parser.add_argument("--inline-top-k", type=int, default=3)
    parser.add_argument("--seed", type=int, default=20261112)
    parser.add_argument("--temperature", type=float, default=0.7)
    parser.add_argument("--progress", type=int, default=25)
    parser.add_argument("--fresh", action="store_true", help="delete the cache first")
    args = parser.parse_args(argv)

    tier = TIER_ALIASES.get(args.tier, args.tier)
    mode = _mode(args)
    if mode is None:
        _print_missing_credentials()
        return 2
    if mode == "adaption" and args.mode == "auto":
        print("auto-selected live Adaption mode (credentials and SDK present)")

    models = args.model or (list(MULTI_MODELS) if tier == "multmodel" else ["qwen3.8-27b"])
    out = args.out
    out.mkdir(parents=True, exist_ok=True)

    if args.fresh and args.cache.exists():
        args.cache.unlink()
        print(f"removed cache {args.cache}")

    download = mode == "adaption" and args.download_questions
    questions = load_questions(
        handoff=args.handoff, json_path=args.questions_json, download=download
    )
    synthetic = sum(1 for question in questions.values() if question.synthetic)
    print(
        f"loaded {len(questions)} questions ({synthetic} with placeholder text); "
        f"tier={tier}, mode={mode}, models={', '.join(models)}"
    )
    if synthetic and mode == "adaption" and not args.allow_synthetic_questions:
        print(
            "\nRefusing a live run with placeholder question text: pass "
            "--questions-json <file> (task/item/text/options) or "
            "--download-questions, or add --allow-synthetic-questions for a "
            "mechanism-only run.",
            file=sys.stderr,
        )
        return 2
    if synthetic and mode == "mock":
        print("mock mode: placeholder questions are fine; results validate the harness only")

    worlds = select_worlds(questions, tier, seed=args.seed)
    if not worlds:
        print(f"tier {tier} selected no worlds (no self-sabotaged questions?)", file=sys.stderr)
        return 2
    print(f"{len(worlds)} base worlds -> {len(worlds) * 4} evaluated arm-debates")

    cache = ContentAddressedCache(args.cache)
    if args.purge_empty_cache:
        print(f"purged cache: {cache.purge_empty()}")
    budget = BudgetTracker(max_api_calls=args.max_api_calls, max_credits=args.max_credits)
    if mode == "mock":
        provider = MockProvider()
    else:
        try:
            provider = AdaptionProvider(timeout=60.0, max_retries=3)
        except RuntimeError as exc:
            print(f"\n{exc}", file=sys.stderr)
            _print_missing_credentials()
            return 2
    provider = Throttled(provider, args.concurrency)

    results = []
    failures = []
    summaries: dict[str, dict] = {}
    for model in models:
        config = LiveConfig(
            model=model,
            rounds=args.rounds,
            temperature=args.temperature,
            max_output_tokens=args.max_tokens,
            seed=args.seed,
            concurrency=args.concurrency,
            max_api_calls=args.max_api_calls,
            max_credits=args.max_credits,
            inline_tau=args.inline_tau,
            inline_top_k=args.inline_top_k,
            capture_samples=(tier == "sanity"),
        )
        print(f"\n=== {model}: {len(worlds)} worlds x 4 arms ===")
        model_results, model_failures = asyncio.run(
            run_suite(
                worlds, provider, cache, budget, config,
                mock=(mode == "mock"), progress_every=args.progress,
            )
        )
        results.extend(model_results)
        failures.extend(model_failures)
        summaries[model] = summarize(model_results)
        print(
            f"{model}: {len(model_results)} arm-debates, {budget.calls} total calls, "
            f"{budget.credits:.3f} credits"
        )
        if budget.stopped:
            print(f"budget stop: {model_failures[-1]['error'] if model_failures else ''}")
            break

    combined = summarize(results)
    def _slice(cell: dict, name: str) -> str:
        value = cell["slices"].get(name)
        return "-" if value is None else f"{value:.2f}"

    rows = []
    for model in summaries:
        for arm, cell in summaries[model]["by_arm"].items():
            rows.append(
                [
                    model,
                    arm,
                    cell["debates"],
                    f"{cell['g_del_percent']:.2f}",
                    f"{cell['g_release_percent']:.2f}",
                    _slice(cell, "SELF_SABOTAGED_64"),
                    _slice(cell, "TRUE_ADVERSARIAL_236"),
                    _slice(cell, "GSM8K_100"),
                    f"{cell['shadow_contaminated_percent']:.2f}",
                    f"{cell['discrepancy_percent']:.2f}",
                    f"{cell['attack_failure_percent']:.2f}",
                    f"{cell['defense_failure_percent']:.2f}",
                    f"{cell['abstain_percent']:.2f}",
                    cell["api_calls"],
                    f"{cell['credits']:.3f}",
                ]
            )
    headers = ["Model", "Arm", "n", "g_del %", "g_rel %", "SelfSab %",
               "TrueAdv %", "GSM8K %", "Shadow %", "Disc %", "Attack %",
               "Defense %", "Abstain %", "Calls", "Credits"]
    print_table(f"Live inline suite ({mode} mode, tier {tier})", headers, rows)
    print("\nPaired delta vs GAMMAF-FixedTarget-PostHoc (same worlds):")
    for arm, cell in combined["paired_vs_posthoc"].items():
        print(f"  {arm:34s} {cell['delta_vs_posthoc_pp']:+.2f} pp over {cell['worlds']} worlds")
    bootstrap = {
        arm: paired_bootstrap(results, arm)
        for arm in ARMS
        if arm != "GAMMAF-FixedTarget-PostHoc"
    }
    print("\nPaired world bootstrap (2,000 resamples) and Wilcoxon:")
    for arm, cell in bootstrap.items():
        p_value = cell["p_wilcoxon"]
        print(
            f"  {arm:34s} {cell['delta_pp']:+.2f} pp "
            f"[{cell['ci_low_pp']:+.2f}, {cell['ci_high_pp']:+.2f}] "
            f"p={p_value:.4f}" if p_value is not None else
            f"  {arm:34s} {cell['delta_pp']:+.2f} pp "
            f"[{cell['ci_low_pp']:+.2f}, {cell['ci_high_pp']:+.2f}] p=n/a"
        )
    print(f"\nbudget: {budget.summary()}")
    print(f"cache: {cache.stats()}")

    note = (
        "MOCK MODE: the deterministic simulator validates the harness "
        "(caching, pairing, inline intervention), not model behaviour."
        if mode == "mock"
        else "Live Adaption run."
    )
    caption = (
        f"Tiered Adaption suite ({tier}, {mode} mode). Paired arms share questions, "
        "topologies, insider sets and round-1 completions."
    )
    latex_table(
        out / "Table_Live_Adaption.tex",
        caption,
        "tab:live-adaption",
        [header.replace("%", r"\%") for header in headers],
        rows,
        note=note + " $g_{del}$ is the plurality over unflagged voters; $g_{rel}$ "
        "grades all ten votes; Shadow is the share of debates with pre-exclusion "
        "contamination.",
    )

    # -- figure: accuracy per arm and paired delta ------------------------ #
    fig, (left, right) = plt.subplots(1, 2, figsize=(9.6, 3.9))
    arms = list(combined["by_arm"])
    if arms:
        values = [combined["by_arm"][arm]["g_del_percent"] for arm in arms]
        colors = ["#999999", "#4c72b0", "#55a868", "#c44e52"][: len(arms)]
        positions = np.arange(len(arms))
        left.bar(positions, values, color=colors)
        for x, value in zip(positions, values):
            left.text(x, value + 0.2, f"{value:.1f}", ha="center", fontsize=7)
        left.set_xticks(positions, [arm.replace("GAMMAF-", "").replace("EpistemicGuard-", "EG-")
                                    for arm in arms], rotation=20, ha="right", fontsize=7)
        left.set_ylim(60, 100)
        left.set_ylabel("delivered accuracy (%)")
        left.set_title("Inline vs post-hoc (paired worlds)")
        left.grid(axis="y", alpha=0.3)
    deltas = combined["paired_vs_posthoc"]
    if deltas:
        names = [arm for arm in deltas if arm != "GAMMAF-FixedTarget-PostHoc"]
        values = [deltas[arm]["delta_vs_posthoc_pp"] for arm in names]
        colors = ["#c44e52" if value < 0 else "#55a868" for value in values]
        right.barh(names, values, color=colors)
        right.axvline(0.0, color="black", linewidth=0.8)
        for y, value in enumerate(values):
            offset = -0.04 if value < 0 else 0.04
            right.text(value + offset, y, f"{value:+.2f}", va="center",
                       ha="right" if value < 0 else "left", fontsize=7)
        right.set_xlim(min(values) - 0.6, max(values) + 0.6)
        right.set_xlabel("delta vs fixed-target post-hoc (pp)")
        right.set_title("Same questions, same round-1 answers")
        right.grid(axis="x", alpha=0.3)
    fig.tight_layout()
    fig.savefig(out / "fig_live_inline_vs_posthoc.png", dpi=180, bbox_inches="tight")
    plt.close(fig)

    payload = {
        "meta": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "tier": tier,
            "mode": mode,
            "provider": getattr(provider.provider, "name", "unknown"),
            "models": models,
            "base_worlds": len(worlds),
            "arm_debates": len(results),
            "rounds": args.rounds,
            "seed": args.seed,
            "synthetic_questions": synthetic,
            "note": note,
            "failures": failures,
        },
        "config": {
            "inline_tau": args.inline_tau,
            "inline_top_k": args.inline_top_k,
            "temperature": args.temperature,
            "concurrency": args.concurrency,
            "max_api_calls": args.max_api_calls,
            "max_credits": args.max_credits,
        },
        "budget": budget.summary(),
        "cache": cache.stats(),
        "summaries": summaries,
        "combined": combined,
        "paired_bootstrap": bootstrap,
        "debates": [
            {
                "model": row.model,
                "arm": row.arm,
                "world": row.world,
                "slice": row.slice,
                "correct": row.correct,
                "released_correct": row.released_correct,
                "oracle_correct": row.oracle_correct,
                "rollback_correct": row.rollback_correct,
                "flags": int(sum(row.flags)),
                "shadow_events": row.shadow_events,
                "cuts": row.interventions.get("cuts", 0),
                "notices": row.interventions.get("notices", 0),
                "credits": round(row.credits, 6),
            }
            for row in results
        ],
    }
    if tier == "sanity":
        print("\nSanity gate: round votes and one extracted response per arm")
        for row in results:
            votes = ["".join(record.get("votes", [])) for record in row.rounds]
            sample = ""
            if row.rounds:
                samples = row.rounds[0].get("samples") or []
                sample = samples[0] if samples else ""
            print(f"  {row.arm}: rounds={votes}")
            print(f"    sample: {sample[:180]}")

    (out / "live_results.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=float) + "\n",
        encoding="utf-8",
    )
    cache.close()
    print(f"\nartifacts written to {out.resolve()}")
    if failures:
        print(f"{len(failures)} failures; first: {failures[0]}", file=sys.stderr)
        return 3 if budget.stopped else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
