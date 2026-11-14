"""Concrete regressions from independent review; original tests stay unchanged."""
import copy
import unittest

from source_contract_gateway import (SourceRegistry, TransportCapture,
    canonical_bytes, run_entrypoint, source_sha256)


class GatewayFixRegressionTests(unittest.TestCase):
    def attempt(self, *, source_id='case40', delivered_id='case40', metric=None,
                response_edit=None):
        source = {'id': source_id, 'problem_type': 'free-form', 'prompt': 'Q?',
                  'context': 'None', 'target': ['A']}
        key = ('40', source_sha256(source))
        registry = SourceRegistry.from_selected([{'source_index': 40,
            'source_sha256': key[1], 'record': source}])
        row = copy.deepcopy(source)
        row['id'] = delivered_id
        calls = []
        def transport(request):
            calls.append(request)
            raw = {'id': 'id', 'object': 'chat.completion', 'model': 'qwen3.8-27b',
                'choices': [{'index': 0, 'finish_reason': 'stop', 'message': {
                    'role': 'assistant', 'content': 'A'}}]}
            if response_edit:
                response_edit(raw)
            return TransportCapture(200, request.body, canonical_bytes(raw), 'unit fixture')
        options = {} if metric is None else {
            'metric_adapter': lambda row: copy.deepcopy(metric), 'scorer_sha256': 'a' * 64}
        result = run_entrypoint(registry, key, source, source['target'], transport,
                                delivered_row=row, **options)
        self.assertEqual(result['transport_calls'], len(calls))
        return result

    def test_registry_identity_is_separate_from_record_id(self):
        self.assertEqual(self.attempt()['status'], 'VERIFIED_WITHOUT_METRIC')

    def test_bad_source_ids_fail_before_dispatch(self):
        for ident in (True, False, None, 40.0, [], {}, {'a': 1}, '', ' ', -1):
            with self.subTest(ident=ident):
                result = self.attempt(source_id=ident, delivered_id=ident)
                self.assertEqual(result['transport_calls'], 0)
                self.assertEqual(result['status'], 'INVALID')

    def test_only_canonical_integer_normalization_is_allowed(self):
        for source_id, delivered_id in (('40', 40), (40, '40'), (0, '0'), ('40.0', '40.0')):
            self.assertEqual(self.attempt(source_id=source_id, delivered_id=delivered_id)['status'],
                             'VERIFIED_WITHOUT_METRIC')
        for source_id, delivered_id in (('True', True), ('None', None), ('40.0', 40.0),
                                       ('040', 40), ('40 ', 40), ('40', True)):
            self.assertEqual(self.attempt(source_id=source_id, delivered_id=delivered_id)['transport_calls'], 0)

    def test_provider_errors_never_yield_final(self):
        for error in ({}, {'message': 'failed'}, None, False):
            result = self.attempt(response_edit=lambda raw: raw.update(error=error))
            self.assertEqual(result['status'], 'INCOMPLETE')
            self.assertNotIn('provider_final_content', result)

    def test_unsupported_assistant_payloads_fail_closed(self):
        for key, value in (('tool_calls', [{'id': 'tool'}]), ('function_call', {'name': 'f'}),
                           ('audio', {'id': 'audio'}), ('refusal', 'refused'),
                           ('annotations', [{'type': 'citation'}])):
            with self.subTest(key=key):
                result = self.attempt(response_edit=lambda raw: raw['choices'][0]['message'].update({key: value}))
                self.assertEqual(result['status'], 'INCOMPLETE')
                self.assertNotIn('provider_final_content', result)

    def test_count_schema_and_metric_consistency(self):
        for count in (-1, True, '1', 2):
            result = self.attempt(metric={'primary_metric_result': {'score': 0, 'scored_samples': count},
                                         'primary_metric_details': [0]})
            self.assertEqual(result['status'], 'UNSCORABLE')
        for aggregate, detail in ((1, 0), (2, 2), (-1, -1)):
            result = self.attempt(metric={'primary_metric_result': {'score': aggregate},
                                         'primary_metric_details': [detail]})
            self.assertEqual(result['status'], 'UNSCORABLE')
        result = self.attempt(metric={'num_samples': 1, 'primary_metric_result': {
            'score': 1, 'scored_samples': 1, 'total_samples': 1, 'invalid_references': 0,
            'valid_predictions': None}, 'primary_metric_details': [1]})
        self.assertEqual(result['status'], 'SCORED')


if __name__ == '__main__':
    unittest.main()
