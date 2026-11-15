"""Phase 3 live engine, exercised entirely offline with the deterministic mock."""

from __future__ import annotations

import asyncio
import sqlite3

import numpy as np
import pytest

from gammaf_epistemic.live_adaption import (
    ARMS,
    BudgetTracker,
    Completion,
    ContentAddressedCache,
    LiveConfig,
    MockProvider,
    Question,
    build_world,
    complete_cached,
    compose_completion,
    extract_completion_parts,
    load_questions,
    parse_answer,
    parse_vote,
    run_suite,
    run_world,
    select_worlds,
    summarize,
)


def _question(item=0, *, gold="A", target="A", task="MMLU", dataset_options="ABCD"):
    return Question(
        task=task,
        item=item,
        text="Which option is correct?",
        options=tuple(dataset_options),
        gold=gold,
        buggy_target=target,
        self_sabotaged=target == gold,
        insiders=(0, 1, 2),
    )


def test_parse_answer_variants():
    assert parse_answer("<answer>B</answer>", ("A", "B"), "MMLU") == "B"
    assert parse_answer("I pick <answer>c</answer>.", ("A", "B", "C"), "MMLU") == "C"
    assert parse_answer("<answer>Z</answer>", ("A", "B"), "MMLU") == "ABSTAIN"
    assert parse_answer("no tag", ("A", "B"), "MMLU") == "ABSTAIN"
    assert parse_answer("<answer>1,234</answer>", (), "GSM8K") == "1234"


def test_cache_keys_are_content_addressed(tmp_path):
    cache = ContentAddressedCache(tmp_path / "cache.sqlite")
    messages = [{"role": "user", "content": "hello"}]
    key = cache.make_key("m", messages, 0.7, 256, "salt")
    assert key == cache.make_key("m", messages, 0.7, 256, "salt")
    assert key != cache.make_key("m", messages, 0.2, 256, "salt")
    assert key != cache.make_key("m", messages, 0.7, 512, "salt")
    mode = cache.connection.execute("PRAGMA journal_mode").fetchone()[0]
    assert str(mode).lower() == "wal"
    cache.close()


def test_world_round_trip(tmp_path):
    config = LiveConfig(model="mock", rounds=3)
    world = build_world(_question(), "chain", 7)
    cache = ContentAddressedCache(tmp_path / "cache.sqlite")
    budget = BudgetTracker()
    provider = MockProvider()

    result = asyncio.run(
        run_world(world, ARMS[0], provider, cache, budget, config, mock=True)
    )
    assert result.arm == ARMS[0]
    assert len(result.rounds) == 3
    assert len(result.votes) == 10
    assert result.api_calls == 30
    assert result.cached_calls == 0
    assert result.target == world.buggy_target

    # A second run is served entirely from the checkpoint.
    again = asyncio.run(
        run_world(world, ARMS[0], provider, cache, budget, config, mock=True)
    )
    assert again.api_calls == 0 and again.votes == result.votes
    cache.close()


def test_round_one_is_shared_across_arms(tmp_path):
    config = LiveConfig(model="mock", rounds=3)
    world = build_world(_question(target="B"), "chain", 11)
    cache = ContentAddressedCache(tmp_path / "cache.sqlite")
    budget = BudgetTracker()
    provider = MockProvider()

    async def run():
        results = []
        for arm in ARMS:
            results.append(
                await run_world(world, arm, provider, cache, budget, config, mock=True)
            )
        return results

    results = asyncio.run(run())
    buggy, posthoc, rollback, inline = results
    # Arm 1 pays for all three rounds. In arm 2 the 7 honest round-1 prompts
    # are shared with arm 1, while the 3 insiders carry a different target.
    assert buggy.api_calls == 30
    # All 7 honest round-1 prompts are shared with arm 1; some later neighbour
    # prompts also coincide, so arm 2 pays strictly less than a full rerun.
    assert 7 <= posthoc.api_calls < 30
    assert posthoc.cached_calls >= 7
    # Rollback replays the post-hoc arm with zero calls.
    assert rollback.api_calls == 0
    assert rollback.votes == posthoc.votes
    assert inline.api_calls <= 10
    assert budget.calls == 30 + posthoc.api_calls + inline.api_calls
    cache.close()


def test_inline_arm_cuts_edges(tmp_path):
    config = LiveConfig(
        model="mock", rounds=3, inline_tau=0.0, inline_top_k=3, clean_rounds_to_restore=2
    )
    world = build_world(_question(target="B"), "star", 3)
    cache = ContentAddressedCache(tmp_path / "cache.sqlite")
    budget = BudgetTracker()

    result = asyncio.run(
        run_world(world, ARMS[3], MockProvider(), cache, budget, config, mock=True)
    )
    assert result.interventions["cuts"] >= 1
    # Some sender must be cut before the final round.
    early_flags = [sum(record["flags"]) for record in result.rounds[:-1]]
    assert max(early_flags) >= 1
    cache.close()


def test_budget_cap_stops_the_run(tmp_path):
    config = LiveConfig(model="mock", rounds=3)
    world = build_world(_question(), "chain", 5)
    cache = ContentAddressedCache(tmp_path / "cache.sqlite")
    budget = BudgetTracker(max_api_calls=5)

    results, failures = asyncio.run(
        run_suite([world], MockProvider(), cache, budget, config, mock=True)
    )
    assert budget.stopped is True
    assert failures and "cap" in failures[0]["error"]
    assert len(results) < 4
    cache.close()


def test_resume_never_repays(tmp_path):
    config = LiveConfig(model="mock", rounds=2)
    worlds = [build_world(_question(item=item, target="B"), "chain", item) for item in range(2)]
    cache = ContentAddressedCache(tmp_path / "cache.sqlite")
    budget = BudgetTracker()
    provider = MockProvider()

    first, _ = asyncio.run(run_suite(worlds, provider, cache, budget, config, mock=True))
    calls_after_first = budget.calls
    assert calls_after_first > 0

    second, failures = asyncio.run(
        run_suite(worlds, provider, cache, BudgetTracker(), config, mock=True)
    )
    assert not failures
    assert len(second) == len(first)
    assert sum(row.api_calls for row in second) == 0
    cache.close()


def test_summary_and_paired_deltas(tmp_path):
    config = LiveConfig(model="mock", rounds=2)
    worlds = [build_world(_question(item=item, target="B"), "chain", item) for item in range(3)]
    cache = ContentAddressedCache(tmp_path / "cache.sqlite")
    results, _ = asyncio.run(
        run_suite(worlds, MockProvider(), cache, BudgetTracker(), config, mock=True)
    )
    summary = summarize(results)
    assert set(summary["by_arm"]) == set(ARMS)
    assert summary["paired_vs_posthoc"][ARMS[0]]["worlds"] == 3
    for cell in summary["by_arm"].values():
        assert 0.0 <= cell["g_del_percent"] <= 100.0
        assert cell["debates"] == 3
    cache.close()


def test_tier_sizes_and_determinism():
    questions = {
        (task, item): _question(
            item,
            task=task,
            gold="1" if task == "GSM8K" else "A",
            target="1" if task == "GSM8K" else "A",
            dataset_options="" if task == "GSM8K" else "ABCD",
        )
        for task in ("MMLU", "MMLUPRO", "CSQA", "GSM8K")
        for item in range(100)
    }
    smoke = select_worlds(questions, "smoke")
    assert len(smoke) == 16
    full = select_worlds(questions, "full400")
    assert len(full) == 1_600
    multi = select_worlds(questions, "multmodel")
    assert len(multi) == 80 * 4
    sanity = select_worlds(questions, "sanity")
    assert len(sanity) == 1
    assert [world.key for world in full] == [world.key for world in select_worlds(questions, "full400")]


def test_question_loader_offline(debates):
    questions = load_questions(download=False)
    assert len(questions) == 400
    sabotaged = [q for q in questions.values() if q.self_sabotaged]
    assert len(sabotaged) == 64
    assert all(q.synthetic for q in questions.values())
    assert all(q.options == tuple("ABCDEFGHIJ"[: len(q.options)]) or q.task == "GSM8K" for q in questions.values())


def test_extract_reasoning_only_completion():
    from types import SimpleNamespace

    response = SimpleNamespace(
        output=[
            {
                "type": "reasoning",
                "summary": [{"type": "summary_text", "text": "The answer must be B because of the second clue."}],
            },
            {"type": "message", "content": [{"type": "output_text", "text": ""}]},
        ],
        output_text="",
        usage=SimpleNamespace(input_tokens=100, output_tokens=256),
    )
    content, reasoning = extract_completion_parts(response)
    assert content == ""
    assert "second clue" in reasoning
    text = compose_completion(content, reasoning)
    assert text and "second clue" in text
    assert parse_vote(text, ("A", "B"), "MMLU") == "B"


def test_compose_keeps_both_channels():
    text = compose_completion("FINAL_ANSWER: C", "reasoning here")
    assert text.startswith("")
    assert "reasoning here" in text and "FINAL_ANSWER: C" in text


def test_empty_completion_is_not_cached_and_falls_back(tmp_path):
    class Scripted:
        name = "scripted"

        def __init__(self, replies):
            self.replies = list(replies)
            self.calls = 0

        async def complete(self, model, messages, temperature, max_tokens, salt):
            reply = self.replies[min(self.calls, len(self.replies) - 1)]
            self.calls += 1
            return Completion(reply, 10, 5)

    provider = Scripted(["", "VOTE: B"])
    cache = ContentAddressedCache(tmp_path / "cache.sqlite")
    budget = BudgetTracker()
    completion = asyncio.run(
        complete_cached(
            provider,
            cache,
            budget,
            LiveConfig(model="x"),
            [{"role": "user", "content": "q"}],
            options=("A", "B"),
            task="MMLU",
        )
    )
    assert provider.calls == 2
    assert budget.calls == 2
    assert parse_vote(completion.text, ("A", "B"), "MMLU") == "B"
    assert cache.stats()["completions"] == 1
    cache.close()


def test_empty_only_completion_writes_nothing(tmp_path):
    class Empty:
        name = "empty"

        async def complete(self, model, messages, temperature, max_tokens, salt):
            return Completion("", 10, 5)

    cache = ContentAddressedCache(tmp_path / "cache.sqlite")
    completion = asyncio.run(
        complete_cached(
            Empty(), cache, BudgetTracker(), LiveConfig(model="x"),
            [{"role": "user", "content": "q"}], options=("A", "B"), task="MMLU",
        )
    )
    assert completion.text == ""
    assert cache.stats()["completions"] == 0
    cache.close()


def test_purge_empty_cache(tmp_path):
    cache = ContentAddressedCache(tmp_path / "cache.sqlite")
    cache.connection.execute(
        "INSERT INTO completions VALUES ('k', 'm', '', 0, 0, 0)"
    )
    cache.connection.commit()
    cache.put_completion("k2", "m", Completion("VOTE: A"))
    cache.put_checkpoint("w", "a", {"votes": ["ABSTAIN", "A"], "arm": "a"})
    cache.put_checkpoint("w2", "a", {"votes": ["A"], "arm": "a"})
    removed = cache.purge_empty()
    assert removed == {
        "empty_completions_removed": 1,
        "abstain_checkpoints_removed": 1,
    }
    assert cache.stats()["completions"] == 1
    assert cache.get_checkpoint("w", "a") is None
    assert cache.get_checkpoint("w2", "a") is not None
    cache.close()


def test_loader_reads_dict_options_and_ignores_extras(tmp_path):
    import json as _json

    base = load_questions(download=False)
    mmlu_key = next(key for key in base if key[0] == "MMLU")
    gsm_key = next(key for key in base if key[0] == "GSM8K")
    payload = [
        {
            "task": "MMLU",
            "item": mmlu_key[1],
            "text": "Real MMLU text?",
            "options": {"A": "x", "B": "y", "C": "z", "D": "w"},
        },
        {"task": "GSM8K", "item": gsm_key[1], "text": "Real GSM8K text?", "options": {}},
        {"task": "MMLU-Pro", "item": 999_999, "text": "extra", "options": {}},
    ]
    path = tmp_path / "questions.json"
    path.write_text(_json.dumps(payload), encoding="utf-8")
    loaded = load_questions(json_path=path)
    assert len(loaded) == 400
    assert loaded[mmlu_key].text == "Real MMLU text?"
    assert loaded[mmlu_key].options == ("A", "B", "C", "D")
    assert loaded[mmlu_key].synthetic is False
    assert loaded[gsm_key].options == ()
    assert loaded[gsm_key].synthetic is False


def test_gsm8k_fixed_target_is_a_wrong_integer():
    question = Question(
        task="GSM8K",
        item=1,
        text="How many?",
        options=(),
        gold="13",
        buggy_target="A",
        self_sabotaged=False,
        insiders=(0, 1, 2),
    )
    world = build_world(question, "chain", 5)
    assert world.fixed_target != "13"
    assert world.fixed_target.lstrip("-").isdigit()
    assert world.buggy_target == "A"


def test_round_one_insiders_receive_their_target():
    import gammaf_epistemic.live_adaption as live

    world = build_world(_question(target="B"), "chain", 1)
    votes = ["ABSTAIN"] * 10
    texts = [""] * 10
    insider = live._prompt(
        world, 0, 0, votes, texts, [], "B", None, mock=False
    )
    honest = live._prompt(
        world, 3, 0, votes, texts, [], "B", None, mock=False
    )
    assert "settle on B" in insider[0]["content"]
    assert "settle on" not in honest[0]["content"]


def test_summary_reports_rich_metrics(tmp_path):
    config = LiveConfig(model="mock", rounds=2)
    worlds = [
        build_world(_question(item=item, target="B"), "chain", item)
        for item in range(2)
    ]
    cache = ContentAddressedCache(tmp_path / "cache.sqlite")
    results, _ = asyncio.run(
        run_suite(worlds, MockProvider(), cache, BudgetTracker(), config, mock=True)
    )
    cell = summarize(results)["by_arm"][ARMS[1]]
    for key in (
        "discrepancy_percent",
        "attack_failure_percent",
        "defense_failure_percent",
        "early_gold_percent",
        "abstain_percent",
        "false_credits",
        "missed_credits",
    ):
        assert key in cell
    assert cell["abstain_percent"] == 0.0
    cache.close()

