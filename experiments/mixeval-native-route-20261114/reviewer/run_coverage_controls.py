"""Frozen input/output association guard probes; no provider/model calls.

Run only after the parent commits protocol/runner/control artifacts. These
controls are deliberately malformed derivatives of existing frozen groups.
They do not claim independent scientific observations or transport coverage.
"""
import copy
import hashlib
import json
from pathlib import Path
import sys

P = Path(__file__).resolve().parents[1]
I = P / 'integration'
sys.path.insert(0, str(I))
from native_runner import run_group


def main():
    spec = json.loads((P / 'reviewer/COVERAGE_CONTROLS_PROTOCOL.json').read_text())
    for name, digest in spec['frozen_files'].items():
        assert hashlib.sha256((P / name).read_bytes()).hexdigest() == digest, name
    report = []
    for control in spec['controls']:
        bundle = json.loads((I / 'inputs' / (control['group'] + '.json')).read_text())
        b = copy.deepcopy(bundle)
        name = control['name']
        source_id = next(iter(b['expected_sources']))
        if name == 'missing_output':
            b['outputs'].pop()
        elif name == 'duplicate_source':
            b['records'].append(copy.deepcopy(b['records'][0]))
        elif name == 'duplicate_output':
            b['outputs'].append(copy.deepcopy(b['outputs'][0]))
        elif name == 'altered_expected_source_hash':
            b['expected_sources'][source_id] = '0' * 64
        elif name == 'changed_source_reference':
            r = b['records'][0]
            r['target'] = [(r['target'][0] + 1) % len(r['options'])]
        elif name == 'changed_source_context':
            b['records'][0]['context'] = 'CONTEXT_MUTATION_REVIEWER_CONTROL'
        elif name == 'unsupported_source_type':
            b['records'][0]['problem_type'] = 'unsupported-reviewer-control'
        elif name == 'changed_response_bytes':
            b['outputs'][0]['response'] += '\nRESPONSE_MUTATION_REVIEWER_CONTROL'
        elif name == 'wrong_output_source_association':
            b['outputs'][0]['source_sha256'] = '0' * 64
        elif name == 'preexisting_generated_answer':
            b['records'][0]['generated_ans'] = 'PREEXISTING_REVIEWER_CONTROL'
        else:
            raise ValueError(name)
        output = P / 'reviewer/control-results' / name
        if output.exists():
            raise FileExistsError('Control output exists; do not rerun for activity: ' + name)
        result = run_group(b['records'], b['outputs'], b['expected_sources'], b['expected_responses'], output, b.get('seed', 42))
        error = result.get('error', '')
        passed = (result['status'] == 'INCOMPLETE' and result['typed_rule_mean'] is None
                  and result['generation_calls'] == 0 and result['new_model_calls'] == 0
                  and error.startswith('CoverageError:' + control['expected_error_prefix']))
        report.append({'name': name, 'passed': passed, 'status': result['status'],
                       'error': error, 'typed_rule_mean': result['typed_rule_mean'],
                       'local_generation_batches': result['generation_calls'],
                       'new_model_calls': result['new_model_calls']})
    for name, digest in spec['frozen_files'].items():
        assert hashlib.sha256((P / name).read_bytes()).hexdigest() == digest
    result = {'status': 'PASS' if all(row['passed'] for row in report) else 'FAIL',
              'controls': report, 'source_cohorts_independent': False,
              'source_rows_new': 0, 'provider_model_calls': 0,
              'scope': 'Ten malformed source/output association guard probes on existing frozen cohorts. These are pre-native validation guards; actual request/scoring orchestration is checked separately on the49positive integration cases.'}
    (P / 'reviewer/COVERAGE_CONTROL_VERIFICATION.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
