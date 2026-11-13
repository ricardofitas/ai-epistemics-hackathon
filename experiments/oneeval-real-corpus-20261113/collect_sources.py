"""Acquire a fixed, complete cohort of public released response files; no inference."""
import gzip
import hashlib
import json
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parent

def main():
    manifest = json.loads((ROOT / 'SOURCE_SELECTION.json').read_text())
    output = ROOT / 'capture'
    output.mkdir(exist_ok=True)
    receipts = []
    for item in manifest['files']:
        url = ('https://raw.githubusercontent.com/' + manifest['source_repository'] + '/'
               + manifest['source_commit'] + '/' + item['path'])
        with urllib.request.urlopen(url, timeout=90) as response:
            raw = response.read()
        blob_sha = hashlib.sha1(('blob ' + str(len(raw)) + '\0').encode() + raw).hexdigest()
        assert len(raw) == item['size'], (item['path'], 'size mismatch')
        assert blob_sha == item['git_blob_sha'], (item['path'], 'blob hash mismatch')
        json.loads(raw)
        dataset, name = item['path'].split('/')[-2:]
        destination = output / (dataset + '__' + name + '.gz')
        destination.write_bytes(gzip.compress(raw, mtime=0))
        receipts.append({**item, 'local_file': destination.name,
                         'sha256': hashlib.sha256(raw).hexdigest()})
        print(dataset + '/' + name + ': source identity verified', flush=True)
    (output / 'SOURCE_RECEIPTS.json').write_text(json.dumps(receipts, indent=2) + '\n')
    print('Complete fixed cohort:', len(receipts), flush=True)

if __name__ == '__main__':
    main()
