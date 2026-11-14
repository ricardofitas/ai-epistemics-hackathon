"""Regressions for the two observed whitespace alerts and malformed choices."""
import gzip
import json
from pathlib import Path
import unittest

from choice_adapter import align_preserved_options

ROOT = Path(__file__).resolve().parent / 'artifact/capture'


def load(name, file):
    with gzip.open(ROOT / name / file, 'rt') as stream:
        return [json.loads(line) for line in stream]


class CapturedChoiceNormalization(unittest.TestCase):
    def test_observed_trailing_space_cases_keep_the_same_official_position(self):
        raw = load('mmlu-pro', 'SELECTED.jsonl.gz')
        cases = load('mmlu-pro', 'CHECKER_NATIVE.jsonl.gz')
        for index in [19, 75]:
            source = raw[index]['record']
            result = align_preserved_options(cases[index], source['options'], source['answer_index'])
            self.assertEqual(result['expected_reference'], 'G')
            self.assertEqual(result['correct_text'], result['choices'][6])
            self.assertIsNone(cases[index]['expected_reference'])

    def test_nested_choice_packing_remains_rejected(self):
        raw = load('arc-challenge', 'SELECTED.jsonl.gz')[0]['record']
        case = load('arc-challenge', 'CHECKER_NATIVE.jsonl.gz')[0]
        position = raw['choices']['label'].index(raw['answerKey'])
        result = align_preserved_options(case, raw['choices']['text'], position)
        self.assertEqual(result, case)
        self.assertNotIn(result['correct_text'], result['choices'])

    def test_preserving_equal_choice_texts_keeps_the_declared_index(self):
        record = dict(choices=['same', 'same'], correct_text='same ', expected_reference=None)
        result = align_preserved_options(record, ['same ', 'same '], 1)
        self.assertEqual(result['expected_reference'], 'B')
        self.assertEqual(result['correct_text'], 'same')


if __name__ == '__main__':
    unittest.main()
