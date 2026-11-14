"""Apply the reviewed metadata-only patch to a new runner; replay capture assembly only."""
from pathlib import Path
import ast
import copy
import hashlib
import json

ROOT = Path(__file__).resolve().parent
PRIOR = ROOT.parent / "prior" / "integration"
OLD = '''                score_captures.append({"case_id": key, "source_sha256": expected_sources[key],
                                       "response_sha256": expected_responses[key], **result})'''
NEW = '''                score_detail = dict(result)
                scorer_source_sha256 = score_detail.pop("source_sha256")
                score_captures.append({"case_id": key,
                                       "source_record_sha256": expected_sources[key],
                                       "scorer_source_sha256": scorer_source_sha256,
                                       "response_sha256": expected_responses[key], **score_detail})'''


def main():
    original = (PRIOR / "native_runner.py").read_text()
    assert original.count(OLD) == 1
    patched = original.replace(OLD, NEW)
    target = ROOT / "native_runner_future.py"
    target.write_text(patched)
    ast.parse(patched)
    statement = ast.parse("\n".join(line[16:] for line in NEW.splitlines()))
    executable = compile(statement, str(target), "exec")
    rows = []
    for kind in ("free_form", "multiple_choice"):
        input_path = PRIOR / "inputs" / (kind + ".json")
        result_path = PRIOR / "results" / kind / "RESULT.json"
        inputs = json.loads(input_path.read_text())
        captures = json.loads(result_path.read_text())["score_captures"]
        for capture in captures:
            key = capture["case_id"]
            old_result = {k: v for k, v in capture.items() if k not in ("case_id", "response_sha256")}
            before = copy.deepcopy(old_result)
            environment = {"key": key, "expected_sources": inputs["expected_sources"],
                           "expected_responses": inputs["expected_responses"],
                           "result": old_result, "score_captures": []}
            exec(executable, environment)
            rebuilt = environment["score_captures"][0]
            assert old_result == before
            assert rebuilt["source_record_sha256"] == inputs["expected_sources"][key]
            assert rebuilt["scorer_source_sha256"] == capture["source_sha256"]
            assert rebuilt["response_sha256"] == capture["response_sha256"]
            for field, value in capture.items():
                if field != "source_sha256":
                    assert rebuilt[field] == value
            assert "source_sha256" not in rebuilt
            rows.append(rebuilt)
    assert len(rows) == 49
    (ROOT / "metadata_reconstructed_captures.json").write_text(json.dumps(rows, indent=2, ensure_ascii=False) + "\n")
    result = {"status": "PASS", "capture_assembly_rows": 49,
              "raw_runner_and_results_unchanged": True, "new_native_execution": False,
              "scope": "Exact reviewed metadata patch applied to new runner; only patched capture-construction statements executed on49storedscoring results.",
              "record_hash_and_scorer_hash_separate": True, "all_scores_and_other_capture_fields_unchanged": True,
              "original_runner_sha256": hashlib.sha256(original.encode()).hexdigest(),
              "future_runner_sha256": hashlib.sha256(patched.encode()).hexdigest(),
              "new_model_calls": 0,
              "limitations": "Full runner and provider boundary not rerun; this is metadata assembly verification only."}
    (ROOT / "METADATA_PATCH_VERIFICATION.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
