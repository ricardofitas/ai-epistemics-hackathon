#!/usr/bin/env python3
"""Synthetic offline regression checks. These are not candidate-model findings."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from analyze_hans_target import self_test

ROOT = Path(__file__).resolve().parent


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(',', ':'), allow_nan=False).encode()


def capture(directory, job, text, incomplete=False):
    tid = job['trial_id']
    provider = {'status': 'incomplete' if incomplete else 'completed',
                'output': [{'type': 'message', 'role': 'assistant',
                            'content': [{'type': 'output_text', 'text': text}]}]}
    if incomplete:
        provider['incomplete_details'] = {'reason': 'max_output_tokens'}
    events = [{'event': 'response.completed',
               'data': {'type': 'response.completed', 'response': provider}},
              {'event': 'capture_end', 'http_status': 200,
               'terminal_event': 'response.completed', 'transport_error': None}]
    journal = directory / 'stream_journals' / f'{tid}.jsonl'
    journal.write_text(''.join(json.dumps(e) + '\n' for e in events))
    result = {'trial_id': tid, 'attempt_count': 1,
              'started_utc': '2026-11-13T01:00:01Z', 'ended_utc': '2026-11-13T01:00:02Z',
              'request_payload': job['request_payload'],
              'request_sha256': hashlib.sha256(canonical(job['request_payload'])).hexdigest(),
              'output_text': text, 'output_text_sha256': hashlib.sha256(text.encode()).hexdigest(),
              'http_status': 200, 'response_status': provider['status'],
              'terminal_event': 'response.completed', 'terminal_event_seen': True,
              'used_delta_fallback': False, 'stream_incomplete': False,
              'stream_format_deviation': False, 'completed_nonempty': not incomplete,
              'transport_error': None, 'stream_frame_count': 1, 'stream_json_error_count': 0,
              'stream_journal_sha256': digest(journal), 'raw_response': provider,
              'response_content_type': 'text/event-stream', 'usage': {'cost': 0}}
    (directory / 'api_artifacts' / f'{tid}.json').write_text(json.dumps(result))
    return result


def run():
    checks = self_test()
    with tempfile.TemporaryDirectory() as temporary:
        base = Path(temporary)
        target = base / 'hans_target'
        target.mkdir()
        (base / 'methods').mkdir()
        shutil.copyfile(ROOT.parent / 'methods/capture_audit_source.py',
                        base / 'methods/capture_audit_source.py')
        for name in ['protocol.json', 'manifest.jsonl', 'selected_data.json', 'task_key.json',
                     'source_receipt.json', 'classification_instruction.txt',
                     'official_hans_source_metadata.json',
                     'prepare_hans_target.py']:
            shutil.copyfile(ROOT / name, target / name)
        (target / 'api_artifacts').mkdir()
        (target / 'stream_journals').mkdir()
        jobs = [json.loads(s) for s in (target / 'manifest.jsonl').read_text().splitlines()]
        key = {r['task_id']: r for r in json.loads((target / 'task_key.json').read_text())['rows']}
        captures = []
        for job in jobs:
            predictions = [{'id': k, 'label': 'entailment' if key[k]['gold_binary'] == 'entailment'
                            else 'neutral'} for k in job['task_ids']]
            captures.append(capture(target, job, json.dumps({'predictions': predictions})))
        aggregate = target / 'responses.jsonl'
        def write_aggregate():
            aggregate.write_text(''.join(json.dumps(r) + '\n' for r in captures))
        write_aggregate()
        (target / 'run_metadata.json').write_text(json.dumps({'requested': 40, 'recorded': 40, 'retries': 0}))
        args = [sys.executable, str(ROOT / 'analyze_hans_target.py'), str(target),
                '--freeze-commit', 'a' * 40, '--freeze-time', '2026-11-13T01:00:00Z',
                '--manifest-sha256', digest(target / 'manifest.jsonl'),
                '--protocol-sha256', digest(target / 'protocol.json')]
        subprocess.run(args, capture_output=True, text=True, check=True)
        result = json.loads((target / 'analysis/summary.json').read_text())
        assert result['all_four_candidates_complete']
        assert all(r['accuracy_if_complete'] == 1 for r in result['by_model'].values())
        checks['checks'].append('complete40request320labelsynthetic_workflow')

        # Provider event/status mismatch is an operational incomplete, never eight semantic errors.
        captures[0] = capture(target, jobs[0], '', incomplete=True)
        write_aggregate()
        output = target / 'incomplete_analysis'
        subprocess.run(args + ['--output-directory', str(output)], capture_output=True, text=True, check=True)
        result = json.loads((output / 'summary.json').read_text())
        affected = result['by_model'][jobs[0]['requested_model']]
        assert not result['all_four_candidates_complete'] and affected['missing'] == 8
        assert affected['accuracy_if_complete'] is None
        assert affected['full_cohort_accuracy_bounds'] == [.9, 1]
        checks['checks'].append('incomplete_batch_preserves_fixed_denominator_bounds')

        # Well-captured but malformed output is unscorable, not a second model call or imputed failure.
        captures[0] = capture(target, jobs[0], '{"predictions":[]}')
        write_aggregate()
        output = target / 'invalid_format_analysis'
        subprocess.run(args + ['--output-directory', str(output)], capture_output=True, text=True, check=True)
        result = json.loads((output / 'summary.json').read_text())
        assert result['unscorable_requests'] == 1
        assert result['by_model'][jobs[0]['requested_model']]['missing'] == 8
        checks['checks'].append('malformed_batch_no_output_repair_or_semantic_imputation')

        # A final-text mutation without corresponding SHA/journal changes must stop analysis.
        captures[0]['output_text'] = 'tampered'
        (target / 'api_artifacts' / f"{captures[0]['trial_id']}.json").write_text(json.dumps(captures[0]))
        write_aggregate()
        output = target / 'tamper_analysis'
        result = subprocess.run(args + ['--output-directory', str(output)], capture_output=True, text=True)
        assert result.returncode != 0 and not output.exists()
        checks['checks'].append('tampered_text_rejected_before_output')
    checks['synthetic_checks'] = len(checks['checks'])
    checks['scope'] = 'Synthetic offline predictions derived from source gold solely to test software; no actual classifier calls or performance findings.'
    print(json.dumps(checks))


if __name__ == '__main__':
    run()
