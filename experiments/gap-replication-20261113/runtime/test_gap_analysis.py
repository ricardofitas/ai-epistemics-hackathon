"""Independent finite-cohort checks for source and prediction provenance gates."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest

import analyze_gap
from test_runtime import captured_fixture

class AnalysisIntegrity(unittest.TestCase):
    def test_codec_replay_rejects_hash_consistent_wrong_label(self):
        with tempfile.TemporaryDirectory() as tmp:
            args=captured_fixture(Path(tmp));p=args.directory
            rows=analyze_gap.jsonl(p/'prediction_rows.jsonl');rows[0]['raw_answer']='3'
            (p/'prediction_rows.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows))
            receipt=analyze_gap.load(p/'capture_integrity.json');receipt['prediction_rows_sha256']=analyze_gap.sha(p/'prediction_rows.jsonl')
            (p/'capture_integrity.json').write_text(json.dumps(receipt))
            protocol,_,tasks=analyze_gap.validate_sources(p)
            with self.assertRaisesRegex(ValueError,'codec replay'):analyze_gap.validate_predictions(p,protocol,tasks)
    def test_primary_spec_or_question_tampering_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            args=captured_fixture(Path(tmp));p=args.directory
            original=(p/'primary_spec.json').read_bytes();spec=json.loads(original);spec['primary']['meaningful_threshold_fraction']='0'
            (p/'primary_spec.json').write_text(json.dumps(spec))
            with self.assertRaisesRegex(ValueError,'hash mismatch'):analyze_gap.validate_sources(p)
            (p/'primary_spec.json').write_bytes(original)
            selected=analyze_gap.load(p/'selected_data.json');selected['families'][0]['variants'][0]['question']='Modified after freeze'
            (p/'selected_data.json').write_text(json.dumps(selected))
            with self.assertRaisesRegex(ValueError,'hash mismatch'):analyze_gap.validate_sources(p)
    def test_actual_pipeline_threshold_boundary(self):
        with tempfile.TemporaryDirectory() as tmp:
            args=captured_fixture(Path(tmp),'threshold_boundary')
            with contextlib.redirect_stdout(io.StringIO()):summary=analyze_gap.analyze(args.directory)
            self.assertEqual(summary['primary']['lower_fraction'],'1/10')
            self.assertEqual(summary['primary']['upper_fraction'],'1/10')
            self.assertTrue(summary['primary']['meaningful_replication'])
            self.assertTrue(summary['primary']['positive_identified'])

if __name__=='__main__':unittest.main()
