"""Resume only explicit HTTP-429 rejections, preserving every original attempt."""
import argparse
import base64
import datetime as dt
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent


def load(path):
    return json.loads(path.read_text())


def lines(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def preflight():
    pins = load(ROOT / 'recovery_pins.json')
    for name, expected in pins['files'].items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != expected:
            raise RuntimeError('Frozen recovery file mismatch: ' + name)
    # Reconstruct all original inputs and the first confirmation attempt exactly.
    original_pins = load(ROOT / 'freeze_pins.json')
    unpacked = {**original_pins['unpacked_files'], **pins['unpacked_files']}
    for name, expected in unpacked.items():
        packed = ROOT / (name.replace('/', '_') + '.gz.b64')
        content = gzip.decompress(base64.b64decode(packed.read_text()))
        if hashlib.sha256(content).hexdigest() != expected:
            raise RuntimeError('Packed original input mismatch: ' + name)
        dest = ROOT / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists() and dest.read_bytes() != content:
            raise RuntimeError('Refusing to overwrite an original capture')
        if not dest.exists():
            dest.write_bytes(content)
    requests = lines(ROOT / 'solvers/manifest.jsonl')
    originals = {r['trial_id']: r for r in lines(ROOT / 'initial_solver_capture/responses.jsonl')}
    pending = [r for r in requests if originals[r['trial_id']].get('http_status') == 429]
    expected_ids = load(ROOT / 'RECOVERY_DESIGN.json')['recovery_trial_ids']
    if [r['trial_id'] for r in pending] != expected_ids or len(pending) != 142:
        raise RuntimeError('Recovery selection differs from the recorded HTTP-429 set')
    return requests, originals, pending


def run():
    requests, originals, pending = preflight()
    if os.environ.get('GITHUB_RUN_ATTEMPT') != '1':
        raise RuntimeError('A recovery must not be silently rerun')
    if os.environ.get('GITHUB_REF') != 'refs/heads/ricardo/advice-transfer-rate-recovery-20261113':
        raise RuntimeError('Unexpected recovery branch')
    out = ROOT / 'recovery'
    out.mkdir(exist_ok=False)
    artifacts = out / 'api_artifacts'; journals = out / 'stream_journals'
    artifacts.mkdir(); journals.mkdir()
    spec = importlib.util.spec_from_file_location('original_sse', ROOT / 'scripts/run_adaption_stream_pilot.py')
    runner = importlib.util.module_from_spec(spec); spec.loader.exec_module(runner)
    credential = os.environ['ADAPTION_API_KEY']
    dump(out / 'EXECUTION_RECEIPT.json', {'started_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
         'run_id': os.environ['GITHUB_RUN_ID'], 'execution_commit': os.environ['GITHUB_SHA'],
         'original_trials': 192, 'explicit_429_trials': 142, 'minimum_start_interval_seconds': 5,
         'initial_backoff_seconds': 60, 'maximum_recovery_attempts_per_rejected_trial': 3,
         'only_explicit_429_can_be_retried': True, 'source_cohort_models_prompts_scores_unchanged': True})
    time.sleep(60)
    selected = dict(originals)
    ledger = []
    previous_start = 0.0
    for index, row in enumerate(pending, 1):
        attempt_ids = []
        for recovery_attempt in range(1, 4):
            wait = 5 - (time.monotonic() - previous_start)
            if wait > 0:
                time.sleep(wait)
            previous_start = time.monotonic()
            trial_id = row['trial_id'] + f'-recovery-{recovery_attempt}'
            physical = {**row, 'trial_id': trial_id}
            record = runner.run_trial(physical, credential, 120, artifacts, journals)
            attempt_ids.append(trial_id)
            normalized = {**record, 'trial_id': row['trial_id'], 'physical_capture_id': trial_id,
                          'original_rejected_http_status': 429}
            selected[row['trial_id']] = normalized
            print(json.dumps({'recovered_index': index, 'total_rejected': len(pending),
                              'trial_id': row['trial_id'], 'physical_capture_id': trial_id,
                              'http_status': record.get('http_status'),
                              'completed_nonempty': record.get('completed_nonempty')}), flush=True)
            if record.get('http_status') != 429:
                break
            time.sleep(60)
        ledger.append({'trial_id': row['trial_id'], 'initial_http_status': 429,
                       'recovery_physical_capture_ids': attempt_ids,
                       'selected_physical_capture_id': attempt_ids[-1],
                       'total_http_attempts_including_original': len(attempt_ids) + 1})
    target = ROOT / 'solvers/responses.jsonl'
    if target.exists():
        raise FileExistsError('Refusing to overwrite a derived combined capture')
    target.write_text(''.join(json.dumps(selected[r['trial_id']], ensure_ascii=False) + '\n' for r in requests))
    (out / 'ATTEMPT_LEDGER.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in ledger))
    dump(out / 'SUMMARY.json', {'rejected_originals': len(pending),
         'physical_recovery_calls': sum(len(r['recovery_physical_capture_ids']) for r in ledger),
         'complete_final_task_answers': sum(bool(r.get('completed_nonempty')) for r in selected.values()),
         'original_complete_captures_preserved': sum(r.get('http_status') != 429 for r in originals.values())})
    subprocess.run([sys.executable, str(ROOT / 'study_analysis.py'), str(ROOT)], check=True)


def finalize():
    credential = os.environ.get('ADAPTION_API_KEY', '').encode()
    files = [p for p in ROOT.rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    safe = all(not credential or credential not in p.read_bytes() for p in files)
    with open(os.environ['GITHUB_OUTPUT'], 'a') as handle:
        handle.write('safe=' + str(safe).lower() + '\n')
    if not safe:
        raise RuntimeError('Credential scan failed')
    dump(ROOT / 'RECOVERY_ARTIFACT_INDEX.json', {'files': [{'path': str(p.relative_to(ROOT)),
         'sha256': hashlib.sha256(p.read_bytes()).hexdigest(), 'bytes': p.stat().st_size} for p in sorted(files)],
         'credential_scan_passed': True})


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
