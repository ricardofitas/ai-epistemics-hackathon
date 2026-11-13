"""Offline source admission gate checks; all review fixtures are synthetic."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('p1_source_finalizer', HERE / 'finalize_source_selection.py')
finalizer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(finalizer)
FAMILIES = json.loads((HERE / 'candidate_families.json').read_text())['families']


def fixtures():
    return [{'response_id': f['response_id'], 'source_family_id': f['source_family_id'],
             'family_disposition': 'pass',
             'variant_checks': {v['variant']: {'computed_answer': v['gold_answer'],
                 'gold_status': 'pass',
                 'target_structure_status': 'same' if v['variant'] in ('numeric', 'paraphrase') else 'not_applicable',
                 'arithmetic_evidence': 'SYNTHETIC OFFLINE TEST FIXTURE, NOT A SOURCE REVIEW', 'issue': ''}
                 for v in f['variants']}, 'family_issue': ''} for f in FAMILIES]


def write(path, rows):
    path.write_text(''.join(json.dumps(x) + '\n' for x in rows))


class SourceGateTests(unittest.TestCase):
    def run_gate(self, a, b, root):
        ap, bp, out = root / 'a.jsonl', root / 'b.jsonl', root / 'out'
        write(ap, a); write(bp, b)
        with contextlib.redirect_stdout(io.StringIO()):
            code = finalizer.finalize(HERE, ap, bp, out)
        return code, out

    def test_all_pass_selects_exact_first30_and_common10_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, out = self.run_gate(fixtures(), fixtures(), Path(tmp))
            selected = json.loads((out / 'selected_data.json').read_text())['families']
            self.assertEqual(code, 0)
            self.assertEqual([f['response_id'] for f in selected], [f'P{i:03d}' for i in range(1,31)])
            self.assertEqual([f['batch_block'] for f in selected], [i // 3 + 1 for i in range(30)])
            self.assertTrue(all(f['analysis_role'] == 'replication' for f in selected))
            self.assertEqual([f['variants'] for f in selected], [f['variants'] for f in FAMILIES[:30]])

    def test_uncertainty_reject_and_false_pass_never_overridden(self):
        a, b = fixtures(), fixtures()
        a[0]['family_disposition'] = 'uncertain'
        b[1]['family_disposition'] = 'reject'
        a[2]['variant_checks']['p1_i0']['computed_answer'] = '99999999999999'
        with tempfile.TemporaryDirectory() as tmp:
            code, out = self.run_gate(a, b, Path(tmp))
            ids = [f['response_id'] for f in json.loads((out / 'selected_data.json').read_text())['families']]
            self.assertEqual(code, 0)
            self.assertEqual(ids, [f'P{i:03d}' for i in range(4,34)])

    def test_only29_both_pass_stops_without_creating_cohort(self):
        a, b = fixtures(), fixtures()
        for row in a[29:]: row['family_disposition'] = 'uncertain'
        with tempfile.TemporaryDirectory() as tmp:
            code, out = self.run_gate(a, b, Path(tmp))
            self.assertEqual(code, 2)
            self.assertFalse(out.exists())

    def test_invalid_family_identifier_or_duplicate_stream_stops(self):
        for mutate in ('wrongfamily', 'duplicate'):
            a, b = fixtures(), fixtures()
            if mutate == 'wrongfamily': a[0]['source_family_id'] = 'GSM8K-DOES-NOT-MATCH'
            else: a[1] = a[0].copy()
            with tempfile.TemporaryDirectory() as tmp:
                with self.assertRaises(ValueError): self.run_gate(a, b, Path(tmp))
                self.assertFalse((Path(tmp) / 'out').exists())

    def test_structure_must_be_same_and_arithmetic_evidence_present(self):
        a, b = fixtures(), fixtures()
        a[0]['variant_checks']['numeric']['target_structure_status'] = 'uncertain'
        b[1]['variant_checks']['paraphrase']['arithmetic_evidence'] = ''
        with tempfile.TemporaryDirectory() as tmp:
            code, out = self.run_gate(a, b, Path(tmp))
            ids = [f['response_id'] for f in json.loads((out / 'selected_data.json').read_text())['families']]
            self.assertEqual(ids[0], 'P003')
            self.assertNotIn('P001', ids); self.assertNotIn('P002', ids)

    def test_existing_output_directory_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); (root / 'out').mkdir()
            with self.assertRaises(ValueError): self.run_gate(fixtures(), fixtures(), root)
            self.assertEqual(list((root / 'out').iterdir()), [])


if __name__ == '__main__':
    unittest.main()
