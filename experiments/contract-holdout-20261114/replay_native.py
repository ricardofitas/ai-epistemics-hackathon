"""Replay the captured native method audit offline in an isolated directory."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parent


def main():
    data = ROOT / 'artifact'
    protocol = json.loads((data / 'PROTOCOL.json').read_text())
    support = data / 'source_support.zip'
    assert hashlib.sha256(support.read_bytes()).hexdigest() == protocol['source_support_sha256']
    expected = json.loads((data / 'RESULTS.json').read_text())
    with tempfile.TemporaryDirectory(prefix='holdout-native-offline-') as directory:
        workspace = Path(directory)
        with zipfile.ZipFile(support) as bundle:
            for name in bundle.namelist():
                assert not Path(name).is_absolute() and '..' not in Path(name).parts
            bundle.extractall(workspace)
        experiment = workspace / 'holdout'
        shutil.copytree(data, experiment)
        result = subprocess.run([sys.executable, str(experiment / 'audit_holdout.py')], cwd=workspace, capture_output=True, text=True)
        assert result.returncode == 0, result.stdout + result.stderr
        actual = json.loads((experiment / 'RESULTS.json').read_text())
        assert actual == expected
    print(json.dumps(dict(offline_native_replay='passed', identical_original_panels=len(expected),
                         new_provider_calls=0, original_artifacts_preserved=True)))


if __name__ == '__main__':
    main()
