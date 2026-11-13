"""Run one frozen advice translation/source transfer capture using repository auth."""
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


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def preflight():
    pins = load(ROOT / 'freeze_pins.json')
    for relative, expected in pins['files'].items():
        if sha(ROOT / relative) != expected:
            raise RuntimeError('Frozen file mismatch: ' + relative)
    packed = ROOT / 'reviews_manifest.jsonl.gz.b64'
    manifest = gzip.decompress(base64.b64decode(packed.read_text()))
    if hashlib.sha256(manifest).hexdigest() != pins['reviews_manifest_sha256']:
        raise RuntimeError('Frozen review manifest mismatch')
    (ROOT / 'reviews').mkdir(exist_ok=True)
    target = ROOT / 'reviews/manifest.jsonl'
    if target.exists() and target.read_bytes() != manifest:
        raise RuntimeError('Prior manifest changed')
    if not target.exists():
        target.write_bytes(manifest)
    subprocess.run([sys.executable, str(RUNNER), str(target.parent), '--dry-run'], check=True)
    return pins


def make_solver_manifest():
    disposition, families = source_admission(ROOT)
    solvers = ROOT / 'solvers'
    solvers.mkdir(exist_ok=False)
    dump(solvers / 'source_disposition.json', disposition)
    dump(solvers / 'admitted_families.json', families)
    protocol = load(ROOT / 'transfer/protocol.json')
    manifest = []
    for family in families:
        for variant in family['variants']:
            for model in protocol['solvers']:
                trial = f"ST-{len(manifest) + 1:04d}"
                payload = {'model': model, 'input': protocol['solver_instruction'] + variant['question'],
                           'temperature': 0, 'max_output_tokens': 8192, 'stream': True,
                           'tools': [], 'agentic_memory': False, 'store': False, 'tool_choice': 'none'}
                manifest.append({'trial_id': trial, 'family_id': family['family_id'], 'variant': variant['id'],
                                 'gold': variant['answer'], 'source_row_sha256': variant['source_row_sha256'],
                                 'request_payload': payload, 'request_sha256': hashlib.sha256(canonical(payload)).hexdigest()})
    manifest.sort(key=lambda row: hashlib.sha256(('solver-order:' + row['trial_id']).encode()).hexdigest())
    path = solvers / 'manifest.jsonl'
    path.write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in manifest))
    dump(solvers / 'COHORT_FREEZE.json', {'frozen_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
         'selection_uses_solver_outputs': False, 'families': len(families), 'solver_calls': len(manifest),
         'source_review_sha256': sha(ROOT / 'reviews/responses.jsonl'),
         'manifest_sha256': sha(path), 'source_protocol_sha256': sha(ROOT / 'transfer/protocol.json')})
    print(json.dumps({'source_admitted': len(families), 'new_single_item_solver_calls': len(manifest)}), flush=True)
    return len(manifest)


def run():
    pins = preflight()
    if os.environ.get('GITHUB_RUN_ATTEMPT') != '1':
        raise RuntimeError('Use the captured first attempt; inference must not be silently repeated')
    if os.environ.get('GITHUB_REF') != 'refs/heads/ricardo/advice-execution-transfer-20261113':
        raise RuntimeError('Unexpected execution branch')
    if any((ROOT / 'reviews' / n).exists() for n in ('responses.jsonl', 'api_artifacts', 'stream_journals')) or (ROOT / 'solvers').exists():
        raise FileExistsError('Prior inference capture exists')
    key = os.environ['ADAPTION_API_KEY']
    request = urllib.request.Request('https://api.prod.adaptionlabs.ai/api/v1/models?type=hosted',
                                    headers={'Authorization': 'Bearer ' + key})
    with urllib.request.build_opener(NoRedirect()).open(request, timeout=30) as response:
        catalogue = json.load(response)
    expected = set(load(ROOT / 'transfer/protocol.json')['reviewers'] + load(ROOT / 'transfer/protocol.json')['solvers'])
    available = sorted(r['id'] for r in catalogue.get('data', []) if isinstance(r, dict) and isinstance(r.get('id'), str))
    dump(ROOT / 'catalogue_check.json', {'checked_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
         'required_model_ids': sorted(expected), 'available_model_ids': available,
         'all_present': expected <= set(available), 'inference_requests': 0})
    if not expected <= set(available):
        print(json.dumps({'catalogue_available_ids': available, 'missing_fixed_ids': sorted(expected - set(available))}), flush=True)
        raise RuntimeError('A fixed model is absent from the catalogue; no model requests were made')
    dump(ROOT / 'EXECUTION_RECEIPT.json', {'started_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
         'execution_commit': os.environ['GITHUB_SHA'], 'run_id': os.environ['GITHUB_RUN_ID'],
         'run_attempt': 1, 'pins': pins, 'review_requests': 132, 'maximum_solver_requests': 480,
         'attempts_per_request': 1, 'concurrency': 4, 'no_history_or_tools': True})
    subprocess.run([sys.executable, str(RUNNER), str(ROOT / 'reviews'), '--concurrency', '4'], check=True)
    count = make_solver_manifest()
    if count:
        subprocess.run([sys.executable, str(RUNNER), str(ROOT / 'solvers'), '--concurrency', '4'], check=True)
    subprocess.run([sys.executable, str(ROOT / 'study_analysis.py'), str(ROOT)], check=True)


def finalize():
    credential = os.environ.get('ADAPTION_API_KEY', '').encode()
    files = [p for p in ROOT.rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    safe = all(not credential or credential not in p.read_bytes() for p in files)
    with open(os.environ['GITHUB_OUTPUT'], 'a') as handle:
        handle.write('safe=' + str(safe).lower() + '\n')
    if not safe:
        raise RuntimeError('Artifact secret check failed')
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
