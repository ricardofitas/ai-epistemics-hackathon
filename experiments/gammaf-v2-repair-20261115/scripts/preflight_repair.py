"""Offline checks of the frozen repaired stimulus and paired execution."""
import json
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
capture = root / 'capture'
capture.mkdir(exist_ok=True)
commands = [
    [sys.executable, '-m', 'pytest', '-q', 'tests/test_repaired_live.py', 'tests/test_fixed_population_recount.py', 'tests/test_repaired_analysis.py'],
    [sys.executable, 'scripts/run_repaired_live.py', '--mode', 'prepare'],
    [sys.executable, 'scripts/run_repaired_live.py', '--mode', 'mock', '--out', 'capture/offline_mock'],
]
with (capture / 'offline-preflight.log').open('w') as log:
    for command in commands:
        subprocess.run(command, cwd=root, stdout=log, stderr=subprocess.STDOUT, check=True)
payload = json.loads((capture / 'offline_mock/repaired_results.json').read_text())
assert payload['mode'] == 'mock'
assert len(payload['rows']) == 128
assert payload['summary']['complete_pairs'] == 64
assert not payload['failures']
assert payload['physical_attempts'] == 0
print(json.dumps({'offline_preflight': 'PASS', 'mock_pairs': 64, 'provider_calls': 0}))
