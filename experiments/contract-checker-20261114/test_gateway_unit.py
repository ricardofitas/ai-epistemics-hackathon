"""Small local unit suite; uses no model/network or installed One-Eval modules."""
import copy
import json
from pathlib import Path
import unittest

from source_contract_gateway import (
    ENDPOINT, SourceRegistry, TransportCapture, canonical_bytes,
    run_entrypoint, sha256, source_sha256,
)

ROOT = Path(__file__).resolve().parents[1]


class GatewayUnitTests(unittest.TestCase):
    def setUp(self):
        self.source = {'id': 'x', 'problem_type': 'free-form', 'prompt': 'Q?',
                       'context': 'None', 'target': ['A', 'Alias']}
        self.key = ('x', source_sha256(self.source))
        self.registry = SourceRegistry({self.key: self.source})
        self.calls = []

    def transport(self, request):
        self.calls.append(request)
        raw = {'id': 'response-1', 'object': 'chat.completion', 'model': 'qwen3.8-27b',
               'choices': [{'index': 0, 'finish_reason': 'stop', 'message': {
                   'role': 'assistant', 'content': '\n\nA', 'reasoning_content': 'keep reasoning'}}]}
        return TransportCapture(200, request.body, canonical_bytes(raw), 'local unit fixture')

    def run_case(self, **kwargs):
        return run_entrypoint(self.registry, self.key, self.source,
                              self.source['target'], self.transport, **kwargs)

    def test_verbatim_final_and_isolation(self):
        row = {**copy.deepcopy(self.source), 'generated_ans': '<think>original</think>'}
        original = {'native_metric_runner': {'primary_metric_details': [None]}}
        before = copy.deepcopy((row, original, self.source))
        result = self.run_case(delivered_row=row, original_native_result=original)
        self.assertEqual(result['status'], 'VERIFIED_WITHOUT_METRIC')
        self.assertEqual(result['provider_final_content'], '\n\nA')
        self.assertEqual(result['delivered_row']['generated_ans'], row['generated_ans'])
        self.assertEqual((row, original, self.source), before)
        result['original_native_result']['native_metric_runner']['primary_metric_details'][0] = 4
        self.assertEqual(original, before[1])

    def test_bad_source_reference_and_type_never_dispatch(self):
        for change in ('source', 'reference', 'task', 'provider', 'native_bytes'):
            source = copy.deepcopy(self.source)
            ref = copy.deepcopy(self.source['target'])
            kwargs = {}
            if change == 'source': source['prompt'] = 'changed'
            if change == 'reference': ref = []
            if change == 'task': kwargs['task_type'] = 'choice'
            if change == 'provider': kwargs['provider_type'] = 'responses'
            if change == 'native_bytes': kwargs['native_request_bytes'] = b'{}'
            result = run_entrypoint(self.registry, self.key, source, ref, self.transport, **kwargs)
            self.assertIn(result['status'], ('INVALID', 'INCOMPLETE'))
            self.assertEqual(result['transport_calls'], 0)
        self.assertEqual(self.calls, [])

    def test_invalid_trusted_aliases(self):
        source = copy.deepcopy(self.source)
        source['target'] = ['']
        key = ('x', source_sha256(source))
        result = run_entrypoint(SourceRegistry({key: source}), key, source, [''], self.transport)
        self.assertEqual(result['failures'], ['invalid_alias_reference'])
        self.assertEqual(self.calls, [])

    def test_duplicate_id_and_callback_mutation(self):
        self.assertEqual(self.run_case()['status'], 'VERIFIED_WITHOUT_METRIC')
        result = self.run_case()
        self.assertEqual(result['failures'], ['duplicate_response_id'])

    def test_metric_zero_requires_row_eligibility(self):
        def metric(row):
            row['target'].append('mutated')
            return {'primary_metric_result': {'score': 0.0}, 'primary_metric_details': [None]}
        result = self.run_case(metric_adapter=metric, scorer_sha256='a' * 64)
        self.assertEqual(result['status'], 'UNSCORABLE')
        self.assertNotIn('eligible_metric_score', result)
        self.assertEqual(result['delivered_row']['target'], ['A', 'Alias'])
        self.assertEqual(self.source['target'], ['A', 'Alias'])

    def test_eligible_metric_zero_is_known(self):
        result = self.run_case(metric_adapter=lambda row: {
            'primary_metric_result': {'score': 0.0}, 'primary_metric_details': [0.0]},
            scorer_sha256='a' * 64)
        self.assertEqual(result['status'], 'SCORED')
        self.assertEqual(result['eligible_metric_score'], 0.0)

    def test_wire_mismatch_blocks_metric(self):
        def transport(request):
            capture = self.transport(request)
            return TransportCapture(200, b'wrong', capture.response_bytes, 'fixture')
        result = run_entrypoint(self.registry, self.key, self.source, self.source['target'], transport,
                                metric_adapter=lambda _: self.fail('metric must not run'), scorer_sha256='a' * 64)
        self.assertEqual(result['failures'], ['actual_request_binding_mismatch'])
        self.assertEqual(result['metric_calls'], 0)

    def test_archived_source_typed_exact_wire_hashes(self):
        selected = json.loads((ROOT / 'real/selected2.json').read_text())
        registry = SourceRegistry.from_selected(selected)
        for entry in selected:
            trace = json.loads((ROOT / f"real/results/real/{entry['source_index']}_source_typed/HTTP_TRACE.json").read_text())[0]
            result_path = ROOT / f"real/results/real/{entry['source_index']}_source_typed/RESULT.json"
            original = json.loads(result_path.read_text())
            actual = json.dumps(trace['request_payload'], allow_nan=False).encode()
            self.assertEqual(sha256(actual), trace['request_sha256'])
            def archive(request):
                self.assertEqual(request.body, actual)
                return TransportCapture(trace['http_status'], actual, trace['response_body'].encode(),
                                        'archived HTTP_TRACE', trace['method'], trace['url'])
            source = entry['record']
            result = run_entrypoint(registry, (str(entry['source_index']), entry['source_sha256']),
                                    source, source['target'], archive,
                                    native_request_bytes=actual, delivered_row=original['delivered_row'],
                                    original_native_result=original)
            self.assertEqual(result['status'], 'VERIFIED_WITHOUT_METRIC')
            self.assertEqual(result['request_sha256'], trace['request_sha256'])
            self.assertEqual(result['response_sha256'], trace['body_sha256'])
            self.assertEqual(result['original_native_result'], original)


if __name__ == '__main__':
    unittest.main()
