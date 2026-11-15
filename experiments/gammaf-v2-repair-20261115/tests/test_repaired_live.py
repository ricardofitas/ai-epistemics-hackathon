import asyncio
import importlib.util
import json
from pathlib import Path

import pytest

from gammaf_epistemic.live_adaption import (
    BudgetExceeded, Completion, LiveConfig, Question, _prompt,
    _provider_call, build_world, ContentAddressedCache,
)

spec = importlib.util.spec_from_file_location("repaired_runner", Path(__file__).parents[1] / "scripts/run_repaired_live.py")
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


def source_files(tmp_path):
    questions, population = [], []
    for task, n in {"MMLU": 28, "CSQA": 21, "MMLUPRO": 15}.items():
        for item in range(n):
            questions.append({"task": task, "item": item, "gold": "B", "text": "Which material is magnetic?",
                              "options": {"A": "Wood", "B": "Iron", "C": "Glass", "D": "Paper"}})
            population.append({"task": task, "item": item, "gold": "B", "buggy_target": "B", "insiders": [2, 4, 8]})
    q, p = tmp_path / "questions.json", tmp_path / "population.json"
    q.write_text(json.dumps(questions)); p.write_text(json.dumps({"source_commit": runner.SOURCE_SHA, "question_count": 64, "questions": population}))
    return q, p


def test_full_options_reach_both_prompt_classes_and_cache_identity():
    q = Question(task="MMLU", item=1, text="Which material is magnetic?", options=("A", "B"),
                 gold="B", buggy_target="B", self_sabotaged=True, insiders=(2, 4, 8),
                 option_texts=(("A", "Wood"), ("B", "Iron")))
    w = build_world(q, "chain", 19)
    for block in (q.prompt_block(), w.prompt_block()):
        assert "[A] Wood" in block and "[B] Iron" in block
        assert "gold" not in block.lower()
    for agent in range(10):
        actual = _prompt(w, agent, 0, ["ABSTAIN"] * 10, [""] * 10, [], w.fixed_target, None, mock=False)
        assert "[A] Wood" in actual[1]["content"] and "[B] Iron" in actual[1]["content"]
        assert "MOCK_CTX" not in actual[1]["content"]
    prompt = _prompt(w, 0, 0, ["ABSTAIN"] * 10, [""] * 10, [], w.fixed_target, None, mock=False)
    assert "[A] Wood" in prompt[1]["content"]
    assert "PRIVATE TARGET" not in prompt[1]["content"]
    changed = [dict(m) for m in prompt]
    changed[1]["content"] = changed[1]["content"].replace("Iron", "Copper")
    assert ContentAddressedCache.make_key("m", prompt, .7, 1024, "new") != ContentAddressedCache.make_key("m", changed, .7, 1024, "new")


def test_panel_deterministic_stratified_complete_and_wrong_target(tmp_path):
    q, p = source_files(tmp_path)
    manifest = runner.make_manifest(q, p)
    assert len(manifest["questions"]) == 32
    assert len(manifest["worlds"]) == 64
    assert all(w["fixed_target"] != w["gold"] for w in manifest["worlds"])
    assert {task: sum(r["task"] == task for r in manifest["questions"]) for task in runner.QUOTAS} == runner.QUOTAS
    old_ids = [(r["task"], r["item"]) for r in manifest["questions"]]
    q.write_text(json.dumps(list(reversed(json.loads(q.read_text())))))
    pr = json.loads(p.read_text()); pr["questions"].reverse(); p.write_text(json.dumps(pr))
    assert [(r["task"], r["item"]) for r in runner.make_manifest(q, p)["questions"]] == old_ids


def test_prepare_is_idempotent_after_json_round_trip(tmp_path, monkeypatch):
    import sys
    q, p = source_files(tmp_path)
    target = tmp_path / "manifest.json"
    monkeypatch.setattr(sys, "argv", ["run_repaired_live.py", "--mode", "prepare", "--questions", str(q), "--population", str(p), "--manifest", str(target)])
    assert runner.main() == 0
    before = target.read_bytes()
    assert runner.main() == 0
    assert target.read_bytes() == before


@pytest.mark.parametrize("issue", ["blank", "missing_gold", "gold_mismatch", "bad_insiders"])
def test_fail_closed_for_invalid_stimuli_or_identity(tmp_path, issue):
    q, p = source_files(tmp_path)
    qr, pop = json.loads(q.read_text()), json.loads(p.read_text()); pr = pop["questions"]
    if issue == "blank":
        qr[0]["options"]["A"] = "  "
    elif issue == "missing_gold":
        del qr[0]["options"]["B"]
    elif issue == "gold_mismatch":
        pr[0]["gold"] = "A"
    else:
        pr[0]["insiders"] = [2, 2, 8]
    q.write_text(json.dumps(qr)); p.write_text(json.dumps(pop))
    with pytest.raises(ValueError):
        runner.make_manifest(q, p)


def test_primary_pairing_and_missing_outcomes_are_not_failure_labels():
    worlds = [{"task": "MMLU", "item": i, "graph": g, "seed": i} for i in range(2) for g in runner.GRAPHS]
    outcomes = [(0, 1), (1, 0), (1, 1), (0, None)]
    rows = []
    for world, (a, b) in zip(worlds, outcomes):
        key = f"{world['task']}:{world['item']}:{world['graph']}:{world['seed']}"
        rows.append({"world": key, "arm": runner.ARMS[0], "correct": bool(a)})
        if b is not None:
            rows.append({"world": key, "arm": runner.ARMS[1], "correct": bool(b)})
    summary = runner.pair_summary(worlds, rows, bootstrap=50)
    assert summary["complete_pairs"] == 3
    assert summary["gained_correct"] == summary["lost_correct"] == 1
    assert summary["all_planned_delta_bounds_pp"] == [0, 25]
    assert len(summary["missing"]) == 1
    assert summary["complete_question_clusters"] == 1


class Fake:
    name = "fake"
    def __init__(self, fail=False):
        self.calls = 0; self.fail = fail
    async def complete(self, *args):
        self.calls += 1
        if self.fail:
            raise RuntimeError("simulated timeout")
        return Completion("VOTE: B", 50, 10)


def test_failed_physical_requests_count_and_persist_across_resume(tmp_path):
    path = tmp_path / "ledger.jsonl"
    async def exercise():
        raw = Fake(fail=True)
        provider = runner.BoundedProvider(raw, path, interval=0, max_attempts=2)
        config = LiveConfig(model="qwen3.8-27b", max_retries=3)
        with pytest.raises(BudgetExceeded):
            await _provider_call(provider, config, [{"role": "user", "content": "Question"}])
        assert raw.calls == provider.attempts == 2
        resumed_raw = Fake()
        resumed = runner.BoundedProvider(resumed_raw, path, interval=0, max_attempts=2)
        with pytest.raises(BudgetExceeded):
            await resumed.complete("qwen3.8-27b", [{"role": "user", "content": "Question"}], .7, 1024, "x")
        assert resumed_raw.calls == 0
        assert resumed.attempts == 2
    asyncio.run(exercise())


def test_request_count_is_atomic_under_concurrency(tmp_path):
    async def exercise():
        raw = Fake()
        provider = runner.BoundedProvider(raw, tmp_path / "ledger.jsonl", interval=0, max_attempts=3)
        attempts = await asyncio.gather(*(provider.complete("qwen3.8-27b", [{"role": "user", "content": "Q"}], .7, 1024, "s") for _ in range(10)), return_exceptions=True)
        assert sum(isinstance(x, Completion) for x in attempts) == 3
        assert raw.calls == provider.attempts == 3
    asyncio.run(exercise())


def test_sdk_retries_can_be_disabled_for_physical_attempt_accounting(monkeypatch):
    import sys
    import types
    from gammaf_epistemic.live_adaption import AdaptionProvider
    observed = {}
    class SDK:
        def __init__(self, **kwargs):
            observed.update(kwargs)
    monkeypatch.setitem(sys.modules, "adaption", types.SimpleNamespace(AsyncAdaption=SDK))
    AdaptionProvider(api_key="unit-test-dummy", timeout=90, max_retries=0)
    assert observed["max_retries"] == 0


def test_fatal_provider_authentication_error_stops_before_retry(tmp_path):
    class AuthenticationError(RuntimeError):
        status_code = 401
    class Unauthenticated(Fake):
        async def complete(self, *args):
            self.calls += 1
            raise AuthenticationError("sensitive mock credential text")
    async def exercise():
        raw = Unauthenticated()
        path = tmp_path / "ledger.jsonl"
        provider = runner.BoundedProvider(raw, path, interval=0)
        with pytest.raises(BudgetExceeded):
            await _provider_call(provider, LiveConfig(max_retries=3), [{"role": "user", "content": "Q"}])
        assert raw.calls == 1 and provider.stopped
        assert "sensitive mock credential text" not in path.read_text()
    asyncio.run(exercise())
