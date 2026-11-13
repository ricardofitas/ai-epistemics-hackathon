"""Offline integration fixture: opposite selectors plus an unknown confirmation item."""
import contextlib
import hashlib
import importlib.util
import io
import itertools
import json
from pathlib import Path
import tempfile
import unittest
import shutil


HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("math_analysis_fixture", HERE / "analyze_math.py")
analysis = importlib.util.module_from_spec(spec)
spec.loader.exec_module(analysis)


def dump(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def dump_rows(path, rows):
    path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fixture(root):
    names = list(analysis.EXPECTED_MODELS)
    families, tasks, requests, predictions = [], [], [], []
    for i in range(30):
        role = "selection" if i < 15 else "confirmation"
        block = (i % 15) // 3 + 1
        family = {"source_family_id": f"F{i:02d}", "analysis_role": role,
                  "selection_slot": i + 1, "batch_block": block,
                  "variants": [{"variant": v, "question": "Synthetic input only",
                                "gold_answer": "1"} for v in analysis.VARIANTS]}
        families.append(family)
        for v in analysis.VARIANTS:
            tasks.append({"task_id": f"T{len(tasks) + 1:04d}",
                          "family_id": family["source_family_id"],
                          "analysis_role": role, "variant": v,
                          "batch_block": block, "gold_answer": "1"})
    for model, role, variant, block in itertools.product(
            names, analysis.ROLES, analysis.VARIANTS, range(1, 6)):
        ids = [r["task_id"] for r in tasks if r["analysis_role"] == role
               and r["variant"] == variant and r["batch_block"] == block]
        requests.append({"trial_id": f"R{len(requests) + 1:03d}",
                         "requested_model": model, "analysis_role": role,
                         "variant": variant, "batch_block": block,
                         "item_ids": ids, "request_payload": {"model": model}})
    for model, task in itertools.product(names, tasks):
        target = task["variant"] in ("numeric", "paraphrase")
        correct = (model == names[1]) if target else (model == names[0])
        unknown = (model == names[1] and task["analysis_role"] == "confirmation"
                   and task["family_id"] == "F15" and task["variant"] == "numeric")
        predictions.append({"model": model, "task_id": task["task_id"],
                            "score_lower": 0 if unknown else int(correct),
                            "score_upper": 1 if unknown else int(correct),
                            "capture_complete": not unknown, "format_valid": not unknown,
                            "label": "unknown" if unknown else "valid" if correct else "wrong",
                            "parsed_answer": None if unknown else "1" if correct else "2"})
    dump(root / "selected_data.json", {"families": families})
    dump(root / "task_key.json", {"rows": tasks})
    dump_rows(root / "manifest.jsonl", requests)
    pins = {n: digest(root / n) for n in
            ("selected_data.json", "task_key.json", "manifest.jsonl")}
    dump(root / "protocol.json", {"models": names, "source_sha256": pins,
                                  "allocation": {k: v for k, v in analysis.COHORT.items()
                                                 if k not in ("unique_items", "blocks_per_split")},
                                  "bootstrap": {"repeats": 10000, "seed": 9}})
    dump_rows(root / "prediction_rows.jsonl", predictions)
    dump(root / "capture_integrity.json", {
        "status": "capture_verified", "protocol_sha256": digest(root / "protocol.json"),
        "manifest_sha256": digest(root / "manifest.jsonl"),
        "prediction_rows_sha256": digest(root / "prediction_rows.jsonl"),
        "planned_requests": 80, "predictions": 240})
    return names


class AnalysisIntegration(unittest.TestCase):
    def test_pinned_codec_rederives_raw_numeric_answer(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            fixture(root)
            shutil.copyfile(HERE / "scoring.py", root / "scoring.py")
            protocol = json.loads((root / "protocol.json").read_text())
            protocol["implementation_sha256"] = {"scoring.py": digest(root / "scoring.py")}
            dump(root / "protocol.json", protocol)
            rows = analysis.jsonl(root / "prediction_rows.jsonl")
            for row in rows:
                row["raw_answer"] = row["parsed_answer"]
            # A hash-consistent but wrongly labelled numeric answer must be rejected.
            rows[0]["raw_answer"] = "1" if rows[0]["parsed_answer"] != "1" else "2"
            dump_rows(root / "prediction_rows.jsonl", rows)
            receipt = json.loads((root / "capture_integrity.json").read_text())
            receipt.update(protocol_sha256=digest(root / "protocol.json"),
                           prediction_rows_sha256=digest(root / "prediction_rows.jsonl"))
            dump(root / "capture_integrity.json", receipt)
            protocol, names, _, tasks = analysis.validate_sources(root)
            with self.assertRaisesRegex(ValueError, "codec replay"):
                analysis.validate_predictions(root, protocol, names, tasks)

    def test_source_admission_and_implementation_pins(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            names = fixture(root)
            admission = root / "admission"
            (admission / "api_artifacts").mkdir(parents=True)
            (admission / "stream_journals").mkdir()
            controls, reports = [], []
            for i, model in enumerate(names, 1):
                tid = f"AD-{i:02d}"
                controls.append({"trial_id": tid, "requested_model": model,
                                 "item_ids": ["A001", "A002", "A003"]})
                artifact = admission / "api_artifacts" / (tid + ".json")
                journal = admission / "stream_journals" / (tid + ".jsonl")
                artifact.write_text("Synthetic artifact\n")
                journal.write_text("Synthetic journal\n")
                reports.append({"trial_id": tid, "capture_complete": True,
                                "format_valid": True, "arithmetic_correctness_checked": False,
                                "artifact_sha256": digest(artifact),
                                "journal_sha256": digest(journal)})
            dump_rows(admission / "manifest.jsonl", controls)
            implementation = root / "frozen_implementation.py"
            implementation.write_text("# Synthetic implementation pin\n")
            protocol = json.loads((root / "protocol.json").read_text())
            protocol["source_sha256"]["admission/manifest.jsonl"] = digest(admission / "manifest.jsonl")
            protocol["implementation_sha256"] = {implementation.name: digest(implementation)}
            protocol["admission"] = {"requests": 2, "directory": "admission"}
            dump(root / "protocol.json", protocol)
            gate = {"status": "fail", "gate_passed": False,
                    "protocol_sha256": digest(root / "protocol.json"),
                    "manifest_sha256": digest(admission / "manifest.jsonl"),
                    "planned_requests": 2, "arithmetic_correctness_checked": False,
                    "rows": reports}
            dump(admission / "GATE.json", gate)
            with self.assertRaisesRegex(ValueError, "admission did not pass"):
                analysis.validate_sources(root)
            gate.update(status="pass", gate_passed=True)
            dump(admission / "GATE.json", gate)
            analysis.validate_sources(root)
            implementation.write_text("# Modified after pinning\n")
            with self.assertRaisesRegex(ValueError, "Implementation hash mismatch"):
                analysis.validate_sources(root)

    def test_reversal_preserves_unknown_confirmation_and_blocks(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            names = fixture(root)
            with contextlib.redirect_stdout(io.StringIO()):
                analysis.analyze(root)
            result = json.loads((root / "analysis/summary.json").read_text())
            self.assertEqual(result["selection_choices"]["bad"]["selected_winner"], names[0])
            self.assertEqual(result["selection_choices"]["corrected"]["selected_winner"], names[1])
            self.assertTrue(result["selection_pair_ordering"]["strict_point_ordering_reversal"])
            self.assertTrue(result["selection_pair_ordering"]["ordering_reversal_identified_by_bounds"])
            contrast = result["confirmation"]
            self.assertTrue(contrast["different_selected_candidates"])
            self.assertEqual(contrast["repaired_selected_minus_bad_selected_mean_accuracy_bounds"],
                             [29 / 30, 1])
            self.assertIsNone(contrast["repaired_selected_minus_bad_selected_mean_accuracy_point"])
            self.assertEqual(contrast["joint_target_difference_bounds"], [14 / 15, 1])
            self.assertEqual(result["capture"]["unknown_correctness_items"], 1)
            for unit in ("family", "batch_block"):
                boot = result["bootstrap"]["confirmation"]["corrected"][unit]
                self.assertIsNone(boot["fixed_winner_difference_point_interval95"])
                low, high = boot["fixed_winner_difference_bound_envelope95"]
                self.assertLessEqual(low, 29 / 30)
                self.assertEqual(high, 1)
            self.assertEqual(result["bootstrap"]["confirmation"]["corrected"]
                             ["batch_block"]["unit_count"], 5)
            with self.assertRaisesRegex(ValueError, "no overwrite"):
                with contextlib.redirect_stdout(io.StringIO()):
                    analysis.analyze(root)

    def test_capture_hash_tampering_rejected_before_scoring(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            fixture(root)
            with (root / "prediction_rows.jsonl").open("a") as f:
                f.write("\n")
            protocol, names, _, tasks = analysis.validate_sources(root)
            with self.assertRaisesRegex(ValueError, "provenance mismatch"):
                analysis.validate_predictions(root, protocol, names, tasks)


if __name__ == "__main__":
    unittest.main()
