#!/usr/bin/env python3
"""One-shot P1 gap replication CI wrapper; no request retry or source edits."""
import argparse
import collections
import datetime as dt
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
STUDY = ROOT / 'experiments/gap-replication-20261113/runtime'
RUNNER = ROOT / 'scripts/run_adaption_stream_pilot.py'
PINS_FILE = Path(__file__).with_name('execution_pins.json')
BRANCH = 'ricardo/epistemics-gap-p1-20261113'
REPO = 'ricardofitas/swarm-adaption-hackathon'
WORKFLOW = '.github/workflows/epistemics-gap-p1.yml'
EXECUTION = 'gap-p1-20261113'
RUNNER_HASH = 'c280811c5f685cdc5b254d5097946835428cd87de6ea58218de1e2cad537fe5e'
MODELS = {'gemma-4-31b-it', 'deepseek-v4-flash'}
ROLES = {'replication'}
VARIANTS = {'numeric', 'paraphrase', 'p1_i0', 'p1_i1'}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def write_exclusive(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write('\n')


def check_plan(pins=None, *, require_launch=True):
    pins = load(PINS_FILE) if pins is None else pins
    require(pins.get('execution_id') == EXECUTION, 'Wrong pin execution ID')
    require(re.fullmatch('[0-9a-f]{40}', pins.get('source_freeze_commit', '')) is not None,
            'Source Git freeze commit required')
    for name in ('protocol.json', 'manifest.jsonl'):
        expected = pins.get(name)
        require(isinstance(expected, str) and re.fullmatch('[0-9a-f]{64}', expected)
                and sha(STUDY / name) == expected, 'Frozen study hash mismatch: ' + name)
    require(pins.get('runner_sha256') == RUNNER_HASH and sha(RUNNER) == RUNNER_HASH,
            'Exact frozen native-SSE runner required')
    protocol = load(STUDY / 'protocol.json')
    require(protocol.get('runner_sha256') == RUNNER_HASH, 'Protocol runner changed')
    for table in ('source_sha256', 'implementation_sha256'):
        for relative, expected in protocol.get(table, {}).items():
            path = Path(relative)
            require(not path.is_absolute() and '..' not in path.parts
                    and (STUDY / path).resolve().is_relative_to(STUDY.resolve()),
                    'Unsafe auxiliary source path')
            require(sha(STUDY / path) == expected, 'Frozen auxiliary hash mismatch: ' + relative)
    require(sha(STUDY / 'gate_admission.py') == pins.get('gate_admission_sha256'),
            'Frozen admission gate implementation changed')
    require(sha(STUDY / 'admission/manifest.jsonl') == pins.get('admission_manifest_sha256'),
            'Frozen admission request hash changed')
    allocation = {'families': 30, 'replication': 30,
                  'variants_per_family': 4, 'models': 2, 'batch_size': 3,
                  'requests': 80, 'classifications': 240}
    require(protocol.get('allocation') == allocation, 'Changed allocation')
    inference = protocol['inference']
    for key, value in {'temperature': 0, 'max_output_tokens': 8192, 'concurrency': 2,
                       'socket_timeout_seconds': 120, 'attempts_per_request': 1,
                       'maximum_requested_output_tokens': 655360,
                       'tools': [], 'agentic_memory': False, 'store': False,
                       'history': 'none'}.items():
        require(inference.get(key) == value, 'Changed inference setting: ' + key)
    require(set(protocol['models']) == MODELS and len(protocol['models']) == 2,
            'Changed model configurations')
    spec = importlib.util.spec_from_file_location('frozen_runner', RUNNER)
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    rows, manifest_hash = runner.load_manifest(STUDY)
    admission_rows, _ = runner.load_manifest(STUDY / 'admission')
    require(len(admission_rows) == 2 and
            collections.Counter(r['requested_model'] for r in admission_rows) ==
            collections.Counter({model: 1 for model in MODELS}),
            'Exactly one format-only admission request per candidate required')
    require({r['trial_id'] for r in admission_rows} == {'AD-01', 'AD-02'},
            'Changed admission IDs')
    for row in admission_rows:
        payload = row['request_payload']
        require(payload['model'] == row['requested_model'] and payload['temperature'] == 0
                and payload['max_output_tokens'] == 8192, 'Changed admission request settings')
        try:
            items = json.loads(payload['input'].split('\n\n', 1)[1])
        except (ValueError, IndexError):
            raise RuntimeError('Invalid admission model input') from None
        require(isinstance(items, list) and len(items) == 3
                and {item.get('id') for item in items} == {'A001', 'A002', 'A003'}
                and all(set(item) == {'id', 'question'} for item in items),
                'Changed three-item admission contract')
    require(sum(row['request_payload']['max_output_tokens'] for row in rows + admission_rows)
            == 671744, 'Changed total study plus admission token bound')
    require(len(rows) == 80 and [r['execution_order'] for r in rows] == list(range(1, 81)),
            'Exactly 80 fixed requests in frozen order required')
    require([r['trial_id'] for r in rows] == [f'GR-{i:03d}' for i in range(1, 81)],
            'Changed trial IDs')
    cells = collections.Counter((r['requested_model'], r['analysis_role'], r['variant'], r['batch_block'])
                                for r in rows)
    expected_cells = collections.Counter({(m, role, variant, block): 1
        for m in MODELS for role in ROLES for variant in VARIANTS for block in range(1, 11)})
    require(cells == expected_cells, 'Changed model/role/variant/block allocation')
    families = load(STUDY / 'selected_data.json')['families']
    require(len(families) == 30 and len({f['source_family_id'] for f in families}) == 30,
            'Expected 30 unique source families')
    family_map = {f['source_family_id']: f for f in families}
    tasks = load(STUDY / 'task_key.json')['rows']
    require(len(tasks) == 120 and len({r['task_id'] for r in tasks}) == 120,
            'Expected 120 unique source tasks')
    task_map = {r['task_id']: r for r in tasks}
    seen_by_model = {m: collections.Counter() for m in MODELS}
    block_families = {}
    for row in rows:
        payload = row['request_payload']
        require(payload['model'] == row['requested_model'] and
                payload['temperature'] == 0 and payload['max_output_tokens'] == 8192,
                'Changed request settings')
        ids, fids = row['item_ids'], row['family_ids']
        require(len(ids) == len(set(ids)) == len(fids) == len(set(fids)) == 3,
                'Each request must have three distinct unrelated source families')
        role, variant, block = row['analysis_role'], row['variant'], row['batch_block']
        key = role, block
        previous = block_families.setdefault(key, tuple(fids))
        require(previous == tuple(fids), 'Common request-sharing block changed')
        try:
            model_items = json.loads(payload['input'].split('\n\n', 1)[1])
        except (ValueError, IndexError):
            raise RuntimeError('Invalid standalone model input') from None
        require(isinstance(model_items, list) and len(model_items) == 3,
                'Expected exactly three model-facing items')
        for tid, fid, model_item in zip(ids, fids, model_items):
            require(tid in task_map and fid in family_map, 'Unknown source task/family')
            task, family = task_map[tid], family_map[fid]
            require(task['family_id'] == fid and task['analysis_role'] == role
                    and task['variant'] == variant and task['batch_block'] == block,
                    'Task-key linkage changed')
            require(family['analysis_role'] == role and family['batch_block'] == block,
                    'Source split/block linkage changed')
            source_item = next(v for v in family['variants'] if v['variant'] == variant)
            require(model_item == {'id': tid, 'question': source_item['question']},
                    'Model input contains altered question or extra metadata')
            require(hashlib.sha256(source_item['question'].encode()).hexdigest() ==
                    task['question_sha256'], 'Question byte hash mismatch')
            seen_by_model[row['requested_model']][tid] += 1
    require(len(block_families) == 10, 'Expected ten common three-family blocks')
    for counts in seen_by_model.values():
        require(counts == collections.Counter({tid: 1 for tid in task_map}),
                'Every task must occur exactly once per candidate')
    if require_launch:
        launch = load(STUDY / 'LAUNCH.json')
        require(launch.get('execution_id') == EXECUTION and launch.get('execute_once') is True
                and launch.get('planned_study_attempts') == 80
                and launch.get('planned_admission_attempts') == 2
                and launch.get('maximum_total_attempts') == 82 and launch.get('pins') == pins,
                'Invalid one-shot launch intent')
    return manifest_hash


def history_guard():
    require(os.environ.get('GITHUB_REPOSITORY') == REPO, 'Wrong repository')
    require(os.environ.get('GITHUB_REF') == 'refs/heads/' + BRANCH, 'Wrong branch')
    require(os.environ.get('GITHUB_EVENT_NAME') == 'push', 'Only exact push event supported')
    require(os.environ.get('GITHUB_RUN_ATTEMPT') == '1', 'Rerun forbidden')
    token = os.environ.get('GH_TOKEN')
    require(bool(token), 'Missing read-only Actions metadata token')
    current = int(os.environ['GITHUB_RUN_ID'])
    matching = []
    for page in range(1, 21):
        query = urllib.parse.urlencode({'branch': BRANCH, 'event': 'push', 'per_page': 100, 'page': page})
        request = urllib.request.Request('https://api.github.com/repos/' + REPO + '/actions/runs?' + query,
            headers={'Authorization': 'Bearer ' + token, 'Accept': 'application/vnd.github+json',
                     'X-GitHub-Api-Version': '2022-11-28', 'User-Agent': 'gap-p1'})
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                runs = json.load(response)['workflow_runs']
        except Exception:
            raise RuntimeError('Actions history unavailable; refusing execution') from None
        matching.extend(r['id'] for r in runs if r.get('path', '').split('@')[0] == WORKFLOW)
        if len(runs) < 100:
            break
    else:
        raise RuntimeError('Actions history exceeds pagination bound')
    require(current in matching and set(matching) == {current},
            'Current run absent or prior matching workflow exists; execution forbidden')


def catalog_check():
    """Read-only model metadata; never an availability inference call."""
    credential = os.environ['ADAPTION_API_KEY']
    request = urllib.request.Request('https://api.prod.adaptionlabs.ai/api/v1/models?type=hosted',
        headers={'Authorization': 'Bearer ' + credential, 'User-Agent': 'gap-p1'})
    try:
        with urllib.request.build_opener(NoRedirect()).open(request, timeout=30) as response:
            payload = json.load(response)
    except Exception:
        raise RuntimeError('Provider model catalogue unavailable; zero study requests') from None
    # Retain only documented non-secret catalogue fields, not arbitrary provider strings.
    fields = ('id', 'object', 'owned_by', 'max_input_tokens', 'max_output_tokens', 'display_name', 'mode')
    data = [{k: item[k] for k in fields if k in item} for item in payload.get('data', [])
            if isinstance(item, dict)]
    require(MODELS <= {item.get('id') for item in data}, 'A fixed candidate is unavailable; no substitute')
    sanitized = {'checked_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
                 'endpoint': '/api/v1/models?type=hosted', 'model_inference_calls': 0, 'data': data}
    text = json.dumps(sanitized, ensure_ascii=False)
    require(credential not in text, 'Unexpected credential in catalogue; refusing retention')
    write_exclusive(STUDY / 'provider_catalog.json', sanitized)


def execute():
    manifest_hash = check_plan()
    require(bool(os.environ.get('ADAPTION_API_KEY')), 'Missing ADAPTION_API_KEY; zero study requests')
    history_guard()
    output_names = ('responses.jsonl', 'api_artifacts', 'stream_journals', 'run_metadata.json')
    require(not any((directory / name).exists()
                    for directory in (STUDY, STUDY / 'admission') for name in output_names)
            and not any((STUDY / name).exists() for name in
                        ('ci_execution_receipt.json', 'provider_catalog.json', 'admission/GATE.json')),
            'Prior output exists; no overwrite')
    catalog_check()
    pins = load(PINS_FILE)
    write_exclusive(STUDY / 'ci_execution_receipt.json', {
        'started_utc': dt.datetime.now(dt.timezone.utc).isoformat(), 'execution_id': EXECUTION,
        'run_id': os.environ['GITHUB_RUN_ID'], 'run_attempt': 1,
        'execution_commit': os.environ['GITHUB_SHA'], 'source_freeze_commit': pins['source_freeze_commit'],
        'manifest_sha256': manifest_hash, 'protocol_sha256': pins['protocol.json'],
        'runner_sha256': RUNNER_HASH, 'study_requests_planned': 80,
        'format_only_admission_requests': 2, 'maximum_total_requests': 82,
        'attempts_per_request': 1, 'retries': 0,
        'maximum_study_requested_output_tokens': 655360,
        'maximum_total_requested_output_tokens': 671744,
        'provider_secret_logged': False, 'no_automatic_reexecution': True,
        'catalogue_requests': 1, 'model_availability_inference': 0,
        'format_admission_correctness_is_not_a_gate': True,
        'ci_capture_step_wall_timeout_minutes': 90, 'ci_job_wall_timeout_minutes': 120,
    })
    subprocess.run([sys.executable, str(RUNNER), str(STUDY / 'admission'),
                    '--concurrency', '2', '--timeout', '120'], check=True)
    execution_commit = os.environ['GITHUB_SHA']
    freeze_time = subprocess.check_output(
        ['git', 'show', '-s', '--format=%cI', execution_commit], text=True).strip()
    # A failed strict capture/format gate stops before all study calls. The gate
    # intentionally ignores mathematical correctness of the trivial items.
    subprocess.run([sys.executable, str(STUDY / 'gate_admission.py'), str(STUDY),
                    '--runner', str(RUNNER), '--freeze-commit', execution_commit,
                    '--freeze-time', freeze_time,
                    '--freeze-protocol-sha256', pins['protocol.json']], check=True)
    subprocess.run([sys.executable, str(RUNNER), str(STUDY), '--concurrency', '2', '--timeout', '120'], check=True)


def finalize():
    credential = os.environ.get('ADAPTION_API_KEY', '').encode()
    files = [p for p in STUDY.rglob('*') if p.is_file()]
    safe = all(not credential or credential not in p.read_bytes() for p in files)
    if safe:
        index = [{'path': str(p.relative_to(STUDY)), 'bytes': p.stat().st_size, 'sha256': sha(p)}
                 for p in sorted(files)]
        write_exclusive(STUDY / 'ci_artifact_index.json', {'files': index, 'credential_scan_passed': True})
    with open(os.environ['GITHUB_OUTPUT'], 'a') as output:
        output.write('safe=' + str(safe).lower() + '\n')
    require(safe, 'Credential scan failed; artifact upload suppressed')
    print(json.dumps({'artifact_files_checked': len(files), 'safe_to_upload': safe}))


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('mode', choices=('preflight', 'run', 'finalize'))
    args = p.parse_args()
    if args.mode == 'preflight':
        print(json.dumps({'manifest_sha256': check_plan(), 'planned_study_attempts': 80,
                          'planned_format_only_admission_attempts': 2,
                          'maximum_total_attempts': 82, 'model_calls': 0}))
    elif args.mode == 'run':
        execute()
    else:
        finalize()
