"""Offline capture-integrity fixtures; zero network calls."""
import copy
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import tempfile
from types import SimpleNamespace
import unittest


ROOT = Path(__file__).resolve().parent.parent


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    out = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(out)
    return out


verify = module("capture_verify", ROOT / "ci_source_repair_20261113/verify_capture.py")
runner = module("capture_runner", ROOT / "scripts/run_adaption_stream_pilot.py")


class Result(io.BytesIO):
    status = 200
    headers = {"Content-Type": "text/event-stream"}


class Opener:
    def __init__(self, wire):
        self.wire = wire

    def open(self, request, timeout):
        return Result(self.wire)


class Verification(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "api_artifacts").mkdir()
        (self.root / "stream_journals").mkdir()
        self.row = {"trial_id": "SR-01", "request_payload": {"model": "fixture", "input": "Question?", "stream": True}}
        self.response = {"status": "completed", "output": [{"type": "message", "role": "assistant", "content": [{"type": "output_text", "text": "A bounded answer."}]}]}

    def tearDown(self):
        self.temp.cleanup()

    def capture(self, event="response.completed", response=None, prefix=b""):
        payload = {"type": event, "response": response or self.response}
        wire = prefix + ("event: " + event + "\ndata: " + json.dumps(payload) + "\n\n").encode()
        runner.run_trial(self.row, "offline_fixture", 1, self.root / "api_artifacts", self.root / "stream_journals", Opener(wire))
        return verify.verify_one(self.row, self.root, runner)[2]

    def test_valid_completed_capture(self):
        out = self.capture()
        self.assertTrue(out["capture_complete"], out)
        self.assertEqual(out["integrity_problems"], [])

    def test_contradictory_terminal_event(self):
        # The frozen runner's completed_nonempty flag alone accepts this pair.
        out = self.capture("response.incomplete")
        self.assertTrue(out["artifact_completed_nonempty"])
        self.assertFalse(out["capture_complete"])
        self.assertFalse(out["capture_conditions"]["terminal_completed"])

    def test_contradictory_provider_status(self):
        response = copy.deepcopy(self.response)
        response["status"] = "incomplete"
        out = self.capture(response=response)
        self.assertFalse(out["capture_complete"])
        self.assertFalse(out["capture_conditions"]["provider_completed"])

    def test_malformed_stream_frame(self):
        out = self.capture(prefix=b"event: malformed\ndata: {broken json\n\n")
        self.assertTrue(out["artifact_completed_nonempty"])
        self.assertFalse(out["capture_complete"])
        self.assertFalse(out["capture_conditions"]["no_stream_json_errors"])

    def test_request_payload_tampering(self):
        self.capture()
        path = self.root / "api_artifacts/SR-01.json"
        obj = json.loads(path.read_text())
        obj["request_payload"]["input"] = "Altered question"
        path.write_text(json.dumps(obj))
        out = verify.verify_one(self.row, self.root, runner)[2]
        self.assertFalse(out["capture_complete"])
        self.assertIn("request_payload_mismatch", out["integrity_problems"])

    def test_journal_raw_line_tampering(self):
        self.capture()
        path = self.root / "stream_journals/SR-01.jsonl"
        rows = [json.loads(line) for line in path.read_text().splitlines()]
        rows[0]["raw_lines"][0] = "event: response.failed"
        path.write_text("".join(json.dumps(row) + "\n" for row in rows))
        out = verify.verify_one(self.row, self.root, runner)[2]
        self.assertFalse(out["capture_complete"])
        self.assertIn("journal_SSE_reconstruction_mismatch", out["integrity_problems"])

    def test_missing_artifact_preserved_unscorable(self):
        out = verify.verify_one(self.row, self.root, runner)[2]
        self.assertFalse(out["capture_complete"])
        self.assertIn("missing_artifact", out["integrity_problems"])

    def test_full_packet_excludes_condition_metadata(self):
        source = ROOT / "experiments/impact-study-20261113/source_repair"
        for name in ("protocol.json", "manifest.jsonl"):
            shutil.copyfile(source / name, self.root / name)
        manifest, digest = runner.load_manifest(self.root)
        records = []
        payload = {"type": "response.completed", "response": self.response}
        wire = ("event: response.completed\ndata: " + json.dumps(payload) + "\n\n").encode()
        for row in manifest:
            records.append(runner.run_trial(row, "offline_fixture", 1,
                                           self.root / "api_artifacts", self.root / "stream_journals", Opener(wire)))
        (self.root / "responses.jsonl").write_text("".join(json.dumps(row) + "\n" for row in records))
        (self.root / "run_metadata.json").write_text(json.dumps({
            "manifest_sha256": digest, "requested": 36, "recorded": 36,
            "attempts_per_trial": 1, "concurrency": 2, "socket_timeout_seconds": 120,
            "retries": 0, "transport": "native_sse", "base_url": runner.BASE}))
        args = SimpleNamespace(experiment_dir=self.root,
                               runner=ROOT / "scripts/run_adaption_stream_pilot.py",
                               output_dir=self.root / "review")
        with contextlib.redirect_stdout(io.StringIO()):
            verify.run(args)
        packet = verify.jsonl(args.output_dir / "review_packet.jsonl")
        self.assertEqual(len(packet), 36)
        self.assertEqual({row["response_id"] for row in packet}, {f"I{i:03d}" for i in range(1, 37)})
        self.assertTrue(all(row["capture_complete"] for row in packet))
        self.assertTrue(all(set(row) == {"response_id", "case_id", "original_question", "response", "capture_complete"} for row in packet))
        self.assertEqual(verify.load(args.output_dir / "capture_integrity.json")["strict_complete"], 36)
        self.assertEqual(len(verify.jsonl(args.output_dir / "responses_enriched.jsonl")), 36)
        with self.assertRaises(FileExistsError), contextlib.redirect_stdout(io.StringIO()):
            verify.run(args)


if __name__ == "__main__":
    unittest.main()
