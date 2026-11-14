"""Integration checks on hand-written controls, not a scientific panel rerun."""
import copy
import json
import random

from scoring_adapter import score_case


def run():
    free = dict(problem_type="free-form", benchmark_name="Test", prompt="Name one.",
                target=["cat", "dog"], options=["None"], context=None)
    original = copy.deepcopy(free)
    r = score_case(free, "dog", None)
    assert r["status"] == "PASS" and r["score"] == 1 and not r["random_fallback"]
    assert free == original

    # Preserve a real official-rule limitation, even for a literal target alias.
    counter = dict(free, target=["The result is red"])
    r = score_case(counter, "The result is red", None)
    assert r["score"] == 0 and r["status"] == "PASS"

    choice = dict(problem_type="multiple-choice", benchmark_name="Test",
                  prompt="Choose one.", options=["red", "blue"], target=[0])
    r = score_case(choice, "A.", random.Random(42))
    assert r["score"] == 1 and r["reference"] == "A" and not r["random_fallback"]
    assert score_case(choice, "B", random.Random(42))["score"] == 0

    # Official empty-output fallback remains observed, never forcibly set to0.
    rng = random.Random(42)
    r = score_case(choice, "", rng)
    assert r["random_fallback"] and r["random_draws"] == ["A"]
    assert r["score"] == 1
    assert rng.getstate() == _one_draw_state()

    for target in [[True], [-1], [2], ["0"], [0, 1]]:
        r = score_case(dict(choice, target=target), "A", random.Random(42))
        assert r["status"] == "INCOMPLETE" and r["score"] is None
    assert score_case(dict(free, target=[]), "cat", None)["status"] == "INCOMPLETE"
    assert score_case(dict(free, problem_type="unknown"), "cat", None)["status"] == "INCOMPLETE"
    assert score_case(dict(free, benchmark_name="QuAc"), "cat", None)["status"] == "INCOMPLETE"

    rng = random.Random(42)
    before = rng.getstate()
    r = score_case(choice, None, rng)
    assert r["status"] == "INCOMPLETE" and r["score"] is None
    assert rng.getstate() == before
    return {"status": "PASS", "scope": "Hand-written integration checks; no scientific panel rerun",
            "checks": ["OR aliases", "source immutability", "literal-alias counterexample retained",
                       "zero-based MC reference", "wrong valid letter", "random fallback retained",
                       "RNG consumption", "invalid source fails closed", "missing response unknown"]}


def _one_draw_state():
    rng = random.Random(42)
    rng.choice(["A", "B"])
    return rng.getstate()


if __name__ == "__main__":
    print(json.dumps(run()))
