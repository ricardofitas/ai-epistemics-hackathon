"""Regression cases for blocked inference, unknown checks and label preservation."""
import copy
import unittest

from check_contract import InvalidContract, audit_contract, guarded_inference


def correct_case():
    return dict(schema_version=1, row_id='q1', kind='choice', prompt='What is zero?\nA. 0\nB. one',
                choices=['0', 'one'], correct_text='0', expected_reference='A', reference='A',
                question_probe_changed=True, context_required=False, context_probe_changed=None)


class ContractRegression(unittest.TestCase):
    def test_zero_valued_gold_is_available(self):
        self.assertEqual(audit_contract([correct_case()])['status'], 'PASS')

    def test_shifted_reference_is_rejected(self):
        record = correct_case()
        record['reference'] = 'B'
        report = audit_contract([record])
        self.assertEqual(report['failures']['reference_changed_answer'], 1)

    def test_missing_correct_choice_is_rejected(self):
        record = correct_case()
        record['choices'] = ['two', 'one']
        self.assertEqual(audit_contract([record])['failures']['correct_choice_missing'], 1)

    def test_unknown_question_probe_stays_incomplete(self):
        record = correct_case()
        record['question_probe_changed'] = None
        self.assertEqual(audit_contract([record])['status'], 'INCOMPLETE')

    def test_required_context_probe_cannot_be_ignored(self):
        record = correct_case()
        record.update(context_required=True, context_probe_changed=False)
        self.assertEqual(audit_contract([record])['failures']['context_not_bound'], 1)

    def test_optional_context_is_allowed(self):
        self.assertEqual(audit_contract([correct_case()])['status'], 'PASS')

    def test_empty_cohort_cannot_pass(self):
        self.assertEqual(audit_contract([])['status'], 'INCOMPLETE')

    def test_duplicate_choices_keep_an_explicit_source_index(self):
        record = correct_case()
        record.update(choices=['same', 'same'], correct_text='same', expected_reference='B', reference='B')
        self.assertEqual(audit_contract([record])['status'], 'PASS')

    def test_same_prompt_with_opposite_gold_has_one_inevitable_error(self):
        first = correct_case()
        second = copy.deepcopy(first)
        second.update(row_id='q2', correct_text='one', expected_reference='B', reference='B')
        report = audit_contract([first, second])
        self.assertEqual(report['failures']['conflicting_gold_for_same_prompt_groups'], 1)
        self.assertEqual(report['input_collisions']['minimum_deterministic_errors'], 1)
        self.assertEqual(report['input_collisions']['empirical_prompt_only_accuracy_ceiling'], .5)

    def test_cohort_with_one_answer_position_is_reported(self):
        first, second = correct_case(), correct_case()
        second.update(row_id='q2', prompt='Another zero question\nA. 0\nB. one')
        self.assertTrue(audit_contract([first, second])['attention'])

    def test_invalid_source_adapter_cannot_pass(self):
        record = correct_case()
        record.update(expected_reference='B', reference='B')
        report = audit_contract([record])
        self.assertEqual(report['status'], 'INCOMPLETE')
        self.assertEqual(report['incomplete_checks']['source_adapter_inconsistent'], 1)

    def test_gate_does_not_call_backend_for_an_invalid_contract(self):
        calls = []
        record = correct_case()
        record['question_probe_changed'] = False
        with self.assertRaises(InvalidContract):
            guarded_inference([record], lambda prompts: calls.append(prompts))
        self.assertEqual(calls, [])

    def test_gate_does_not_call_backend_for_an_unknown_check(self):
        calls = []
        record = correct_case()
        record['question_probe_changed'] = None
        with self.assertRaises(InvalidContract):
            guarded_inference([record], lambda prompts: calls.append(prompts))
        self.assertEqual(calls, [])

    def test_valid_contract_preserves_backend_inputs_and_return_value(self):
        calls = []
        def generate(prompts):
            calls.append(prompts)
            return ['<answer>A</answer>']
        self.assertEqual(guarded_inference([correct_case()], generate), ['<answer>A</answer>'])
        self.assertEqual(calls, [[correct_case()['prompt']]])

    def test_freeform_reference_is_supported(self):
        record = correct_case()
        record.update(kind='freeform', choices=None, correct_text='YES', expected_reference='YES', reference='YES')
        self.assertEqual(audit_contract([record])['status'], 'PASS')


if __name__ == '__main__':
    unittest.main()
