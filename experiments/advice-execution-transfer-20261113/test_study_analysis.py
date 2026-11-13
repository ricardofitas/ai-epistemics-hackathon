"""Regression checks for scientific missingness and exact source admission."""
import copy
from fractions import Fraction
import json
from pathlib import Path
import tempfile
import unittest

from study_analysis import number, score_solver, source_admission, response_json


def capture(text, complete=True):
    return {'completed_nonempty': complete, 'response_status': 'completed' if complete else 'incomplete',
            'http_status': 200, 'terminal_event_seen': True, 'stream_incomplete': False,
            'used_delta_fallback': False, 'transport_error': None, 'output_text': text}


class ScientificCodec(unittest.TestCase):
    def test_unknown_capture_is_not_inferred_wrong_from_partial_text(self):
        record = capture('<answer>17</answer>', complete=False)
        self.assertEqual(score_solver(record, '17')[0], (0, 1))
        self.assertIsNone(response_json(capture('{"clarity":"pass"}', complete=False)))

    def test_equivalent_fraction_is_correct_and_wrong_numeric_is_resolved(self):
        self.assertEqual(score_solver(capture('Calculation. <answer>1/2</answer>'), '.5')[0], (1, 1))
        self.assertEqual(score_solver(capture('<answer>2</answer>'), '3')[0], (0, 0))
        self.assertEqual(number('1e-2'), Fraction(1, 100))

    def test_format_and_undefined_fractions_retain_uncertainty(self):
        self.assertIsNone(number('1/0'))
        self.assertIsNone(number('25%'))
        self.assertEqual(score_solver(capture('<answer>2</answer> extra'), '2')[0], (0, 1))
        self.assertEqual(score_solver(capture('<answer>2</answer><answer>2</answer>'), '2')[0], (0, 1))

    def test_either_first_review_can_exclude_without_replacement(self):
        family = {'family_id': 'F1', 'review_id': 'NS-001', 'seed_answer': '5',
                  'variants': [{'id': name, 'answer': '1/2'} for name in
                               ('numeric', 'paraphrase', 'added_operation')]}
        review = {'seed_answer': '5', 'seed_clarity': 'pass',
                  'variants': [{'id': name, 'answer': '.5', 'clarity': 'pass', 'transform_fit': 'pass'}
                               for name in ('numeric', 'paraphrase', 'added_operation')]}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'reviews').mkdir(); (root / 'transfer').mkdir()
            (root / 'transfer/candidate_families.json').write_text(json.dumps([family]))
            def write(second):
                rows = [{**capture(json.dumps(r)), 'trial_id': f'NS-001-R{i}'}
                        for i, r in enumerate([review, second], 1)]
                (root / 'reviews/responses.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in rows))
            write(review)
            self.assertEqual(source_admission(root)[0]['admitted_count'], 1)
            uncertain = copy.deepcopy(review)
            uncertain['variants'][0]['clarity'] = 'uncertain'
            write(uncertain)
            self.assertEqual(source_admission(root)[0]['admitted_count'], 0)
            mismatch = copy.deepcopy(review)
            mismatch['variants'][0]['answer'] = '3/4'
            write(mismatch)
            self.assertEqual(source_admission(root)[0]['admitted_count'], 0)


if __name__ == '__main__':
    unittest.main()
