"""Execute the previously frozen request list in consecutive checkpointed batches."""
import argparse
import base64
import datetime as dt
import gzip
import hashlib
import json
import os
from pathlib import Path
import time
import urllib.request

import run_adaption_stream_pilot as transport

ROOT = Path(__file__).resolve().parent


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')


def preflight():
    protocol = json.loads((ROOT / 'EXECUTION_PROTOCOL.json').read_text())
    for name in ('fresh_panel.jsonl.gz', 'planned_requests.jsonl.gz'):
        decoded = base64.b64decode((ROOT / (name + '.b64')).read_bytes())
        destination = ROOT / name
        if destination.exists():
            assert destination.read_bytes() == decoded
        else:
            destination.write_bytes(decoded)
    cases = ROOT / 'fresh_panel.jsonl.gz'
    assert hashlib.sha256(cases.read_bytes()).hexdigest() == protocol['cases_compressed_sha256']
    raw = gzip.decompress((ROOT / 'planned_requests.jsonl.gz').read_bytes())
    assert hashlib.sha256(raw).hexdigest() == protocol['manifest_uncompressed_sha256']
    manifest = ROOT / 'manifest.jsonl'
    if manifest.exists():
        assert manifest.read_bytes() == raw
    else:
        manifest.write_bytes(raw)
    assert hashlib.sha256((ROOT / 'run_adaption_stream_pilot.py').read_bytes()).hexdigest() == protocol['transport_sha256']
    rows, manifest_hash = transport.load_manifest(ROOT)
    assert len(rows) == protocol['planned_requests'] == 200
    return protocol, rows, manifest_hash


def catalogue():
    protocol, rows, manifest_hash = preflight()
    models = sorted({r['request_payload']['model'] for r in rows})
    credential = os.environ['ADAPTION_API_KEY']
    request = urllib.request.Request(transport.BASE + '/api/v1/models?type=hosted', headers={'Authorization': 'Bearer ' + credential})
    with urllib.request.build_opener(transport.NoRedirect()).open(request, timeout=45) as response:
        status = response.status
        data = json.load(response)
    available = {r.get('id') for r in data.get('data', []) if isinstance(r, dict)}
    write_json(ROOT / 'CATALOGUE_RECEIPT.json', dict(utc=transport.now(), http_status=status, required_models=models,
                required_available=sorted(set(models) & available), manifest_sha256=manifest_hash, model_inference_requests=0))
    assert set(models) <= available, 'A model in the frozen manifest is unavailable'
    print(json.dumps({'catalogue_http_status': status, 'required_models_available': True}), flush=True)


def check_files_for_credential():
    credential = os.environ.get('ADAPTION_API_KEY', '').encode()
    files = sorted(p for p in ROOT.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    assert all(not credential or credential not in p.read_bytes() for p in files), 'Capture contains a credential'
    return files


def run_batch(start, end):
    protocol, rows, manifest_hash = preflight()
    assert os.environ['GITHUB_REF'] == 'refs/heads/' + protocol['execution_branch']
    assert os.environ['GITHUB_RUN_ATTEMPT'] == '1'
    assert 0 <= start < end <= len(rows)
    credential = os.environ['ADAPTION_API_KEY']
    artifacts, journals = ROOT / 'api_artifacts', ROOT / 'stream_journals'
    artifacts.mkdir(exist_ok=True)
    journals.mkdir(exist_ok=True)
    response_path = ROOT / 'responses.jsonl'
    recorded = [json.loads(line) for line in response_path.read_text().splitlines()] if response_path.exists() else []
    assert len(recorded) == start
    assert [r['trial_id'] for r in recorded] == [r['trial_id'] for r in rows[:start]]
    pacing = ROOT / 'PACING.json'
    last_start = json.loads(pacing.read_text())['last_start_epoch'] if pacing.exists() else None
    with response_path.open('a', encoding='utf-8') as output:
        for index in range(start, end):
            row = rows[index]
            assert not (artifacts / (row['trial_id'] + '.json')).exists()
            assert not (journals / (row['trial_id'] + '.jsonl')).exists()
            if last_start is not None:
                time.sleep(max(0, 5 - (time.time() - last_start)))
            last_start = time.time()
            write_json(pacing, {'last_start_epoch': last_start, 'trial_id': row['trial_id']})
            try:
                record = transport.run_trial(row, credential, 120, artifacts, journals)
            except Exception as error:
                # Retain a failed planned trial without issuing another request.
                record = dict(trial_id=row['trial_id'], attempt_count=1, local_capture_error=type(error).__name__,
                              completed_nonempty=False, request_payload=row['request_payload'])
                path = artifacts / (row['trial_id'] + '.json')
                if path.exists():
                    record = json.loads(path.read_text())
                else:
                    transport.atomic_json(path, record)
            output.write(json.dumps(record, ensure_ascii=False) + '\n')
            output.flush()
            os.fsync(output.fileno())
            recorded.append(record)
            print(json.dumps({'progress': index + 1, 'planned': len(rows), 'http_status': record.get('http_status'),
                              'completed_nonempty': record.get('completed_nonempty')}), flush=True)
            if record.get('http_status') == 429:
                time.sleep(60)
    receipt = dict(utc=transport.now(), run_id=os.environ['GITHUB_RUN_ID'], execution_commit=os.environ['GITHUB_SHA'],
                   manifest_sha256=manifest_hash, planned=len(rows), recorded=len(recorded),
                   completed_nonempty=sum(bool(r.get('completed_nonempty')) for r in recorded),
                   policy=protocol['provider_policy'], last_batch=[start, end])
    write_json(ROOT / 'EXECUTION_RECEIPT.json', receipt)
    check_files_for_credential()


def finalize():
    files = check_files_for_credential()
    write_json(ROOT / 'ARTIFACT_INDEX.json', dict(credential_scan_passed=True, files=[
        {'path': str(p.relative_to(ROOT)), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in files]))
    with open(os.environ['GITHUB_OUTPUT'], 'a') as output:
        output.write('safe=true\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['preflight', 'catalogue', 'run', 'finalize'])
    parser.add_argument('--start', type=int)
    parser.add_argument('--end', type=int)
    args = parser.parse_args()
    if args.mode == 'preflight':
        preflight()
    elif args.mode == 'catalogue':
        catalogue()
    elif args.mode == 'run':
        run_batch(args.start, args.end)
    else:
        finalize()
