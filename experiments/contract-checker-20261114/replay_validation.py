"""Replay all captured checker panels with the Python standard library."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

from check_contract import InvalidContract, guarded_inference, read_records

ROOT = Path(__file__).resolve().parent


def main():
    index = json.loads((ROOT / 'PANEL_RESULTS.json').read_text())
    comparisons = []
    for expected in index:
        path = ROOT / expected['input_file']
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected['input_sha256']
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'result.json'
            run = subprocess.run([sys.executable, str(ROOT / 'check_contract.py'), str(path), '--output', str(target)], capture_output=True, text=True)
            observed = json.loads(target.read_text())
            assert run.returncode == {'PASS':0, 'FAIL':1, 'INCOMPLETE':2}[expected['status']]
            for key in ['status', 'counts', 'failures', 'incomplete_checks', 'source_target_counts', 'input_collisions']:
                assert observed[key] == expected[key], (path, key)
        calls = []
        def counter(prompts):
            calls.append(len(prompts))
            return len(prompts)
        try:
            count = guarded_inference(read_records(path), counter)
            assert expected['status'] == 'PASS' and count == expected['counts']['records']
        except InvalidContract:
            assert expected['status'] != 'PASS'
        assert len(calls) == int(expected['status'] == 'PASS')
        comparisons.append({'panel': expected['panel'], 'status': observed['status'], 'records': observed['counts']['records'], 'constructed_backend_calls': len(calls)})
    outcome = {'panels': len(comparisons), 'records_in_replayed_variants': sum(r['records'] for r in comparisons), 'provider_model_calls': 0,
               'passed_panels': sum(r['status'] == 'PASS' for r in comparisons), 'failed_panels': sum(r['status'] == 'FAIL' for r in comparisons), 'all_expected_results_reproduced': True}
    print(json.dumps(outcome, indent=2))


if __name__ == '__main__':
    main()
