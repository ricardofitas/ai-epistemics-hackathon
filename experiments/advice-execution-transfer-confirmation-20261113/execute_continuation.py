"""Execute only the newly admitted, previously untested source families."""
import argparse
import base64
import datetime as dt
import gzip
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import urllib.request

from study_analysis import dump, load, source_admission

ROOT = Path(__file__).resolve().parent
RUNNER = ROOT / 'scripts/run_adaption_stream_pilot.py'


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def preflight():
    pins = load(ROOT / 'freeze_pins.json')
    for name, expected in pins['files'].items():
        if sha(ROOT / name) != expected:
            raise RuntimeError('Frozen file mismatch: ' + name)
    for name, expected in pins['unpacked_files'].items():
        packed = ROOT / (name.replace('/', '_') + '.gz.b64')
        data = gzip.decompress(base64.b64decode(packed.read_text()))
        if hashlib.sha256(data).hexdigest() != expected:
            raise RuntimeError('Packed capture/manifest mismatch: ' + name)
        target = ROOT / name
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists() and target.read_bytes() != data:
            raise RuntimeError('Existing data mismatch: ' + name)
        if not target.exists():
            target.write_bytes(data)
    disposition, admitted = source_admission(ROOT)
    expected_families = load(ROOT / 'solvers/admitted_families.json')
    if admitted != expected_families:
        raise RuntimeError('Amended source admission cannot be independently reconstructed')
    prior = set(load(ROOT / 'ANALYSIS_AMENDMENT.json')['previously_tested_families'])
    if prior & {f['family_id'] for f in admitted}:
        raise RuntimeError('A previously evaluated family entered the confirmation cohort')
    subprocess.run([sys.executable, str(RUNNER), str(ROOT / 'solvers'), '--dry-run'], check=True)
    return pins


def run():
    pins = preflight()
    if os.environ.get('GITHUB_RUN_ATTEMPT') != '1':
        raise RuntimeError('Original first-attempt capture is required')
    if os.environ.get('GITHUB_REF') != 'refs/heads/ricardo/advice-transfer-confirmation-20261113':
        raise RuntimeError('Wrong execution branch')
    if any((ROOT / 'solvers' / name).exists() for name in ['responses.jsonl', 'api_artifacts', 'stream_journals']):
        raise FileExistsError('Prior solver outputs exist')
    credential = os.environ['ADAPTION_API_KEY']
    request = urllib.request.Request('https://api.prod.adaptionlabs.ai/api/v1/models?type=hosted',
                                    headers={'Authorization': 'Bearer ' + credential})
    with urllib.request.build_opener(NoRedirect()).open(request, timeout=30) as response:
        payload = json.load(response)
    available = {r.get('id') for r in payload.get('data', []) if isinstance(r, dict)}
    models = load(ROOT / 'transfer/protocol.json')['solvers']
    if not set(models) <= available:
        raise RuntimeError('A fixed solver is unavailable; no model calls made')
    dump(ROOT / 'EXECUTION_RECEIPT.json', {'started_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
         'run_id': os.environ['GITHUB_RUN_ID'], 'execution_commit': os.environ['GITHUB_SHA'],
         'planned_solver_calls': 192, 'new_advice_or_source_review_calls': 0,
         'families': 16, 'attempts_per_request': 1, 'concurrency': 4, 'pins': pins,
         'original_reviews_reused_without_changes_to_semantic_content': True})
    subprocess.run([sys.executable, str(RUNNER), str(ROOT / 'solvers'), '--concurrency', '4'], check=True)
    subprocess.run([sys.executable, str(ROOT / 'study_analysis.py'), str(ROOT)], check=True)


def finalize():
    credential = os.environ.get('ADAPTION_API_KEY', '').encode()
    files = [p for p in ROOT.rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    safe = all(not credential or credential not in p.read_bytes() for p in files)
    with open(os.environ['GITHUB_OUTPUT'], 'a') as output:
        output.write('safe=' + str(safe).lower() + '\n')
    if not safe:
        raise RuntimeError('Credential scan failed')
    dump(ROOT / 'ARTIFACT_INDEX.json', {'files': [{'path': str(p.relative_to(ROOT)),
         'sha256': sha(p), 'bytes': p.stat().st_size} for p in sorted(files)], 'credential_scan_passed': True})


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['preflight', 'run', 'finalize'])
    args = parser.parse_args()
    if args.mode == 'preflight':
        preflight()
    elif args.mode == 'run':
        run()
    else:
        finalize()
