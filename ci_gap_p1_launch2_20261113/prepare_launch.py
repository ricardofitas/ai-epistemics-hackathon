#!/usr/bin/env python3
"""Bind final reviewed protocol/manifest hashes before CI publication; zero API calls."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
STUDY = ROOT / 'experiments/gap-replication-20261113/runtime'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    with path.open('x', encoding='utf-8') as f:
        json.dump(value, f, indent=2, ensure_ascii=False)
        f.write('\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-freeze-commit', required=True)
    args = parser.parse_args()
    spec = importlib.util.spec_from_file_location('ci_execute', HERE / 'execute.py')
    wrapper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(wrapper)
    pins = {'execution_id': wrapper.EXECUTION, 'source_freeze_commit': args.source_freeze_commit,
            'protocol.json': sha(STUDY / 'protocol.json'),
            'manifest.jsonl': sha(STUDY / 'manifest.jsonl'),
            'admission_manifest_sha256': sha(STUDY / 'admission/manifest.jsonl'),
            'gate_admission_sha256': sha(STUDY / 'gate_admission.py'),
            'runner_sha256': wrapper.RUNNER_HASH}
    wrapper.check_plan(pins, require_launch=False)
    launch = {'execution_id': wrapper.EXECUTION, 'execute_once': True,
              'planned_study_attempts': 80, 'planned_admission_attempts': 2,
              'maximum_total_attempts': 82, 'pins': pins,
              'note': 'Run two fixed format-only admission requests once; only if both pass strict capture/format (not correctness) run the separately frozen 80-row source-reviewed cohort. No retries, replacements, or additional model inference.'}
    write(HERE / 'execution_pins.json', pins)
    write(HERE / 'LAUNCH.template.json', launch)
    print(json.dumps({'pins_written': str(HERE / 'execution_pins.json'),
                      'launch_template': str(HERE / 'LAUNCH.template.json'),
                      'model_calls': 0, 'protocol_sha256': pins['protocol.json'],
                      'manifest_sha256': pins['manifest.jsonl']}))
