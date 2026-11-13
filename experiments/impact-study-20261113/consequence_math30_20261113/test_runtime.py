"""Meaningful offline fixtures for source allocation, JSON codec and strict SSE."""
import argparse
import contextlib
import datetime as dt
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
import shutil

import capture_math
import gate_admission
import prepare_manifest
from scoring import numeric, parse_answers, score_answer

ROOT = Path(__file__).resolve().parent
RUNNER = ROOT.parents[2] / "scripts/run_adaption_stream_pilot.py"
spec = importlib.util.spec_from_file_location("fixture_frozen_runner", RUNNER)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class Result(io.BytesIO):
    status = 200
    headers = {"Content-Type": "text/event-stream"}


class Opener:
    def __init__(self, text, status="completed", malformed=False):
        response = {"id": "offline_fixture", "status": status,
                    "output": [{"type": "message", "role": "assistant", "content": [
                        {"type": "output_text", "text": text}]}]}
        frames = []
        if malformed:
            frames.append("event: response.output_text.delta\ndata: {oops}\n\n")
        frames.append("event: response.completed\ndata: " + json.dumps(
            {"type": "response.completed", "response": response}) + "\n\n")
        self.data = "".join(frames).encode()

    def open(self, request, timeout):
        return Result(self.data)


class NumericAndJSON(unittest.TestCase):
    def test_exact_rational_and_currency_equivalence(self):
        self.assertEqual(numeric("$1,000.00"), numeric("1e3"))
        self.assertEqual(numeric(".5"), numeric("1/2"))
        self.assertEqual(numeric("−4.25"), numeric("-17/4"))
        self.assertNotEqual(numeric("0.333"), numeric("1/3"))

    def test_invalid_numeric_is_unknown_not_wrong(self):
        for value in ("1,23", "1.2.3", "1+2", "NaN", "2 meters", "1e999999", None, 2, "1/0"):
            self.assertEqual(score_answer(value, "2")["score_upper"], 1)
            self.assertFalse(score_answer(value, "2")["format_valid"])
        self.assertEqual(score_answer("ABSTAIN", "2")["score_upper"], 0)

    def test_exact_keyset_and_duplicate_rejection(self):
        self.assertEqual(parse_answers('```json\n{"X":"3","Y":"4"}\n```', ["X", "Y"]), {"X": "3", "Y": "4"})
        for text in ('{"X":"3","X":"4"}', '{"X":"3"}', '{"X":"3","Y":"4","Z":"5"}',
                     'Result: {"X":"3","Y":"4"}', '{"X":NaN,"Y":"4"}'):
            with self.assertRaises(ValueError):
                parse_answers(text, ["X", "Y"])


class CaptureReplay(unittest.TestCase):
    def capture(self, directory, status="completed", malformed=False):
        for name in ("api_artifacts", "stream_journals"):
            (directory / name).mkdir()
        row = {"trial_id": "fixture", "request_payload": {"model": "fixture", "input": "synthetic"}}
        runner.run_trial(row, "OFFLINE-TEST-CREDENTIAL", 1, directory / "api_artifacts",
                         directory / "stream_journals", opener=Opener('{"X":"3"}', status, malformed))
        return row

    def test_completed_replay_and_no_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp); row = self.capture(p)
            _, _, report = capture_math.verify_one(row, p, runner, dt.datetime(2020, 1, 1, tzinfo=dt.timezone.utc))
            self.assertTrue(report["capture_complete"])
            self.assertEqual(report["integrity_problems"], [])

    def test_incomplete_provider_under_completed_event_is_unknown(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp); row = self.capture(p, status="incomplete")
            _, _, report = capture_math.verify_one(row, p, runner, dt.datetime(2020, 1, 1, tzinfo=dt.timezone.utc))
            self.assertFalse(report["capture_complete"])
            self.assertTrue(report["capture_conditions"]["terminal_completed"])
            self.assertFalse(report["capture_conditions"]["provider_completed"])

    def test_json_error_and_tampering_are_not_scored(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp); row = self.capture(p, malformed=True)
            _, _, report = capture_math.verify_one(row, p, runner, dt.datetime(2020, 1, 1, tzinfo=dt.timezone.utc))
            self.assertFalse(report["capture_complete"])
            self.assertFalse(report["capture_conditions"]["no_stream_json_errors"])
            artifact = p / "api_artifacts/fixture.json"
            value = json.loads(artifact.read_text()); value["output_text"] = "tampered"; artifact.write_text(json.dumps(value))
            _, _, report = capture_math.verify_one(row, p, runner, dt.datetime(2020, 1, 1, tzinfo=dt.timezone.utc))
            self.assertIn("output_text_sha256_mismatch", report["integrity_problems"])


class ManifestAllocation(unittest.TestCase):
    def synthetic(self):
        return {"source_validation_status": "accepted_source_reviewed", "families": [
            {"source_family_id": f"SYNTHETIC-{slot}", "selection_slot": slot,
             "analysis_role": "selection" if slot <= 15 else "confirmation",
             "batch_block": ((slot - 1) % 15) // 3 + 1, "source_validation_status": "accepted",
             "variants": [{"variant": v, "question": f"Synthetic {v} problem {slot}: what is 1+1?",
                           "gold_answer": "2"} for v in prepare_manifest.VARIANTS]}
            for slot in range(1, 31)]}

    def test_full_allocation_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp); source = p / "reviewed.json"; source.write_text(json.dumps(self.synthetic()))
            args = argparse.Namespace(selected_data=source, source_manifest=None, runner=RUNNER, output_dir=p / "cohort")
            with contextlib.redirect_stdout(io.StringIO()):
                prepare_manifest.prepare(args)
            manifest, _ = runner.load_manifest(args.output_dir)
            self.assertEqual(len(manifest), 80)
            admission_rows, _ = runner.load_manifest(args.output_dir / "admission")
            self.assertEqual(len(admission_rows), 2)
            self.assertEqual(len({x for row in manifest for x in row["item_ids"]}), 120)
            blocks = {}
            for row in manifest:
                key = row["analysis_role"], row["batch_block"]
                blocks.setdefault(key, row["family_ids"])
                self.assertEqual(blocks[key], row["family_ids"])
                self.assertEqual(len(set(row["family_ids"])), 3)
                self.assertNotIn('gold_answer', row["request_payload"]["input"])
                self.assertNotIn('SYNTHETIC-', row["request_payload"]["input"])
            with self.assertRaises(FileExistsError):
                prepare_manifest.prepare(args)

    def admission_fixture(self, p, malformed=False):
        source = p / "reviewed.json"; source.write_text(json.dumps(self.synthetic()))
        args = argparse.Namespace(selected_data=source, source_manifest=None, runner=RUNNER, output_dir=p / "cohort")
        with contextlib.redirect_stdout(io.StringIO()):
            prepare_manifest.prepare(args)
        for name in json.loads((args.output_dir / "protocol.json").read_text())["implementation_sha256"]:
            shutil.copyfile(ROOT / name, args.output_dir / name)
        admission = args.output_dir / "admission"
        for n in ("api_artifacts", "stream_journals"):
            (admission / n).mkdir()
        rows, _ = runner.load_manifest(admission)
        for i, row in enumerate(rows):
            # Deliberately wrong arithmetic: admission tests only protocol/format.
            text = json.dumps({key: "999" for key in row["item_ids"]})
            if malformed and i == 0:
                text = '{"wrong_id":"999"}'
            runner.run_trial(row, "OFFLINE-TEST-CREDENTIAL", 1, admission / "api_artifacts",
                             admission / "stream_journals", opener=Opener(text))
        return argparse.Namespace(directory=args.output_dir, runner=RUNNER,
            freeze_commit="1" * 40, freeze_time="2020-01-01T00:00:00Z",
            freeze_protocol_sha256=prepare_manifest.sha(args.output_dir / "protocol.json"))

    def test_admission_does_not_test_arithmetic_correctness(self):
        with tempfile.TemporaryDirectory() as tmp:
            args = self.admission_fixture(Path(tmp))
            with contextlib.redirect_stdout(io.StringIO()):
                gate_admission.run(args)
            gate = json.loads((args.directory / "admission/GATE.json").read_text())
            self.assertTrue(gate["gate_passed"])
            self.assertFalse(gate["arithmetic_correctness_checked"])

    def test_admission_bad_ids_stop_without_repair(self):
        with tempfile.TemporaryDirectory() as tmp:
            args = self.admission_fixture(Path(tmp), malformed=True)
            with contextlib.redirect_stdout(io.StringIO()), self.assertRaises(SystemExit):
                gate_admission.run(args)
            self.assertFalse(json.loads((args.directory / "admission/GATE.json").read_text())["gate_passed"])

    def test_full_native_sse_capture_pipeline(self):
        with tempfile.TemporaryDirectory() as tmp:
            args = self.admission_fixture(Path(tmp))
            with contextlib.redirect_stdout(io.StringIO()):
                gate_admission.run(args)
            p = args.directory
            for n in ("api_artifacts", "stream_journals"):
                (p / n).mkdir()
            rows, manifest_hash = runner.load_manifest(p)
            records = []
            for row in rows:
                records.append(runner.run_trial(row, "OFFLINE-TEST-CREDENTIAL", 1,
                    p / "api_artifacts", p / "stream_journals",
                    opener=Opener(json.dumps({key: "2" for key in row["item_ids"]}))))
            (p / "responses.jsonl").write_text("".join(json.dumps(r) + "\n" for r in records))
            (p / "run_metadata.json").write_text(json.dumps({"manifest_sha256": manifest_hash,
                "requested": 80, "attempts_per_trial": 1, "retries": 0}))
            with contextlib.redirect_stdout(io.StringIO()):
                capture_math.run(args)
            receipt = json.loads((p / "capture_integrity.json").read_text())
            self.assertEqual(receipt["strict_complete_requests"], 80)
            self.assertEqual(receipt["known_item_scores"], 240)
            self.assertEqual(receipt["global_issues"], [])
            predictions = [json.loads(x) for x in (p / "prediction_rows.jsonl").read_text().splitlines()]
            self.assertTrue(all(r["score_lower"] == r["score_upper"] == 1 for r in predictions))

    def test_pending_source_review_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp); value = self.synthetic(); value["source_validation_status"] = "pending"
            source = p / "reviewed.json"; source.write_text(json.dumps(value))
            args = argparse.Namespace(selected_data=source, source_manifest=None, runner=RUNNER, output_dir=p / "cohort")
            with self.assertRaises(ValueError):
                prepare_manifest.prepare(args)

    def test_missing_auxiliary_fails_before_manifest_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp); source = p / "reviewed.json"; source.write_text(json.dumps(self.synthetic()))
            args = argparse.Namespace(selected_data=source, source_manifest=p / "absent.json",
                                      runner=RUNNER, output_dir=p / "cohort")
            with self.assertRaises(FileNotFoundError):
                prepare_manifest.prepare(args)
            self.assertFalse((args.output_dir / "manifest.jsonl").exists())
            self.assertFalse((args.output_dir / "task_key.json").exists())


if __name__ == "__main__":
    unittest.main()
