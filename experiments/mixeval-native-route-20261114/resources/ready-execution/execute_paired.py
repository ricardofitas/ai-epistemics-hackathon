"""One-time, source-frozen paired generation with bounded calls and durable SSE receipts."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import time
import tempfile
import urllib.request
import run_adaption_stream_pilot as transport

ROOT = Path(__file__).resolve().parent
canonical = transport.canonical

def write(name, value):
    # Receipts are mutable progress checkpoints. Trial artifacts remain exclusive
    # in the reused transport and must never be overwritten or regenerated.
    target = ROOT / name
    fd, temporary = tempfile.mkstemp(prefix='.' + name + '-', dir=ROOT)
    try:
        with os.fdopen(fd, 'w') as stream:
            json.dump(value, stream, indent=2, ensure_ascii=False)
            stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary): os.unlink(temporary)

def preflight():
    protocol = json.loads((ROOT / 'PROTOCOL.json').read_text())
    for name, digest in protocol['frozen_files'].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, name
    cases = json.loads((ROOT / 'selected20.json').read_text())
    rows, manifest_hash = transport.load_manifest(ROOT)
    assert len(cases) == 20 and len(rows) == 80
    assert len({row['trial_id'] for row in rows}) == 80
    assert sum(row['request_payload']['max_output_tokens'] for row in rows) == 327680
    models = set(protocol['models'])
    expected = {(case['source_index'], condition, model) for case in cases
                for condition in protocol['conditions'] for model in models}
    assert {(row['source_index'], row['condition'], row['request_payload']['model']) for row in rows} == expected
    for row in rows:
        payload = row['request_payload']
        assert payload['temperature'] == 0 and payload['max_output_tokens'] == 4096
        assert len(payload['input'].encode()) <= 8192
        case = next(case for case in cases if case['source_index'] == row['source_index'])
        assert row['source_sha256'] == case['source_sha256']
        assert hashlib.sha256(canonical(case['record'])).hexdigest() == row['source_sha256']
        assert row['prompt_sha256'] == hashlib.sha256(payload['input'].encode()).hexdigest()
        assert case['record']['prompt'] in payload['input']
        if row['condition'] == 'binding_only':
            assert payload['input'] == case['binding_only_prompt']
        else:
            assert payload['input'] == case['official_typed_prompt']
    write('PREFLIGHT_RECEIPT.json', {'status': 'PASS', 'utc': transport.now(),
          'planned_requests': len(rows), 'source_cases': len(cases),
          'maximum_output_tokens': 327680, 'manifest_sha256': manifest_hash,
          'calls_made': 0})
    return protocol, rows, manifest_hash

def run():
    protocol, rows, manifest_hash = preflight()
    assert os.environ.get('GITHUB_RUN_ATTEMPT') == '1'
    assert os.environ.get('GITHUB_REF') == 'refs/heads/' + protocol['execution_branch']
    launch = json.loads((ROOT / 'LAUNCH.json').read_text())
    assert launch['planned_model_calls'] == 80
    assert launch['manifest_sha256'] == manifest_hash
    assert launch['protocol_sha256'] == hashlib.sha256((ROOT / 'PROTOCOL.json').read_bytes()).hexdigest()
    assert all(not (ROOT / name).exists() for name in ['api_artifacts', 'stream_journals', 'responses.jsonl', 'CALL_LEDGER.jsonl'])
    credential = os.environ['ADAPTION_API_KEY']
    request = urllib.request.Request(protocol['catalogue_url'], headers={'Authorization': 'Bearer ' + credential})
    try:
        with urllib.request.build_opener(transport.NoRedirect()).open(request, timeout=30) as response:
            catalogue = json.load(response)
        available = {row.get('id') for row in catalogue.get('data', []) if isinstance(row, dict)}
        required = set(protocol['models'])
        receipt = {'utc': transport.now(), 'required': sorted(required),
                   'required_available': sorted(required & available),
                   'all_available': required <= available, 'model_calls': 0}
        write('CATALOGUE_RECEIPT.json', receipt)
        if not receipt['all_available']:
            write('STOP.json', {'reason': 'fixed_model_unavailable', 'model_calls': 0})
            return
    except Exception as error:
        write('STOP.json', {'reason': 'catalogue_preflight_failed', 'error_type': type(error).__name__, 'model_calls': 0})
        return
    artifacts, journals = ROOT / 'api_artifacts', ROOT / 'stream_journals'
    artifacts.mkdir(); journals.mkdir()
    results = []
    total_input, total_output, last_start = 0, 0, None
    stopped = None
    for row in rows:
        if len(results) >= 80:
            stopped = 'hard_request_cap'; break
        if last_start is not None:
            time.sleep(max(0, 5 - (time.monotonic() - last_start)))
        last_start = time.monotonic()
        intent = {'trial_id': row['trial_id'], 'event': 'attempt_started', 'utc': transport.now(),
                  'attempt_count': 1, 'request_sha256': row['request_sha256']}
        with (ROOT / 'CALL_LEDGER.jsonl').open('a') as stream:
            stream.write(json.dumps(intent) + '\n'); stream.flush(); os.fsync(stream.fileno())
        try:
            result = transport.run_trial(row, credential, 120, artifacts, journals)
        except Exception as error:
            result = {'trial_id': row['trial_id'], 'attempt_count': 1,
                      'local_capture_error': type(error).__name__, 'completed_nonempty': False}
            if not (artifacts / (row['trial_id'] + '.json')).exists():
                transport.atomic_json(artifacts / (row['trial_id'] + '.json'), result)
        results.append(result)
        usage = result.get('usage') or {}
        valid_usage = all(type(usage.get(key)) in (int, float) and usage[key] >= 0
                          for key in ['input_tokens', 'output_tokens'])
        if valid_usage:
            total_input += usage['input_tokens']; total_output += usage['output_tokens']
        with (ROOT / 'CALL_LEDGER.jsonl').open('a') as stream:
            stream.write(json.dumps({'trial_id': row['trial_id'], 'event': 'attempt_recorded',
                         'utc': transport.now(), 'http_status': result.get('http_status'),
                         'completed_nonempty': result.get('completed_nonempty'), 'usage': usage}) + '\n')
            stream.flush(); os.fsync(stream.fileno())
        with (ROOT / 'responses.jsonl').open('a') as stream:
            stream.write(json.dumps(result, ensure_ascii=False) + '\n'); stream.flush(); os.fsync(stream.fileno())
        write('EXECUTION_RECEIPT.json', {'utc': transport.now(), 'run_id': os.environ['GITHUB_RUN_ID'],
              'execution_commit': os.environ['GITHUB_SHA'], 'manifest_sha256': manifest_hash,
              'planned': len(rows), 'recorded': len(results), 'input_tokens': total_input,
              'output_tokens': total_output, 'maximum_output_tokens': 327680,
              'completed_nonempty': sum(bool(r.get('completed_nonempty')) for r in results),
              'attempts_per_request': 1, 'minimum_start_interval_seconds': 5, 'concurrency': 1,
              'cost_currency': None, 'stopped': stopped})
        print(json.dumps({'trial_id': row['trial_id'], 'recorded': len(results),
                          'completed_nonempty': result.get('completed_nonempty')}), flush=True)
        if result.get('http_status') != 200:
            stopped = 'provider_or_transport_error'; break
        if not valid_usage:
            stopped = 'missing_usage'; break
        if usage['output_tokens'] > 4096:
            stopped = 'provider_output_cap_violation'; break
    if stopped:
        write('STOP.json', {'reason': stopped, 'recorded': len(results), 'no_retry': True})
    write('FINAL_CAPTURE_STATUS.json', {'utc': transport.now(), 'planned': 80,
          'recorded': len(results), 'unattempted': 80 - len(results),
          'complete_nonempty': sum(bool(r.get('completed_nonempty')) for r in results),
          'stop_reason': stopped, 'new_model_calls_at_most': len(results)})

def finalize():
    secret = os.environ.get('ADAPTION_API_KEY', '').encode()
    files = [path for path in ROOT.rglob('*') if path.is_file() and '__pycache__' not in path.parts]
    safe = all(not secret or secret not in path.read_bytes() for path in files)
    with open(os.environ['GITHUB_OUTPUT'], 'a') as stream:
        stream.write('safe=' + str(safe).lower() + '\n')
    assert safe, 'Credential scan failed'
    write('ARTIFACT_INDEX.json', {'credential_scan_passed': True, 'files': [
          {'path': str(path.relative_to(ROOT)), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
          for path in sorted(files)]})

if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('mode', choices=['preflight', 'run', 'finalize'])
    mode = parser.parse_args().mode
    if mode == 'preflight': preflight()
    elif mode == 'run': run()
    else: finalize()
