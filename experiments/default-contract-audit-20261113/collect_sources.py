"""Read-only fixed-panel public-source capture; no model calls or credentials."""
import gzip
import hashlib
import io
import json
from pathlib import Path
import time
import tomllib
import urllib.error
import urllib.parse
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'capture'
OUT.mkdir(exist_ok=True)
ATTEMPTS = []

def get(url, limit=80_000_000):
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'research-contract-audit/1.0'})
            with urllib.request.urlopen(req, timeout=90) as response:
                raw = response.read(limit + 1)
                assert len(raw) <= limit, 'source exceeds capture limit'
                ATTEMPTS.append({'url': url, 'attempt': attempt+1, 'status': response.status, 'bytes': len(raw)})
                return raw
        except urllib.error.HTTPError as error:
            ATTEMPTS.append({'url': url, 'attempt': attempt+1, 'status': error.code})
            if error.code in (429, 500, 502, 503, 504) and attempt < 2:
                time.sleep(3 * (attempt + 1))
                continue
            raise

def metadata(repo, revision):
    return json.loads(get('https://huggingface.co/api/datasets/' + repo + '/revision/' + urllib.parse.quote(revision, safe='')))

def capture_dataset(item):
    import pyarrow.parquet as pq
    repo = item['repo']
    current = metadata(repo, 'main')
    parquet_list_url = ('https://huggingface.co/api/datasets/' + repo + '/parquet/'
                        + urllib.parse.quote(item['config'], safe='') + '/' + item['split'])
    parquet_urls = json.loads(get(parquet_list_url))
    assert isinstance(parquet_urls, list) and parquet_urls, parquet_urls
    conversion = metadata(repo, 'refs/convert/parquet')
    rows, files = [], []
    for index, url in enumerate(parquet_urls):
        assert isinstance(url, str)
        url = url.replace('/resolve/refs%2Fconvert%2Fparquet/', '/resolve/' + conversion['sha'] + '/')
        url = url.replace('/resolve/refs/convert/parquet/', '/resolve/' + conversion['sha'] + '/')
        raw = get(url)
        rows.extend(pq.read_table(io.BytesIO(raw)).to_pylist())
        name = item['bench'] + '__' + item['split'] + '__' + str(index) + '.parquet'
        (OUT / name).write_bytes(raw)
        files.append({'file': name, 'url': url, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()})
    row_name = item['bench'] + '__' + item['split'] + '.jsonl.gz'
    payload = ''.join(json.dumps(row, ensure_ascii=False, default=str) + '\n' for row in rows).encode()
    (OUT / row_name).write_bytes(gzip.compress(payload, mtime=0))
    return {**item, 'status': 'captured', 'source_main_commit': current['sha'],
            'converted_parquet_commit': conversion['sha'], 'rows': len(rows), 'files': files,
            'rows_file': row_name, 'rows_sha256': hashlib.sha256(payload).hexdigest()}

def main():
    protocol = json.loads((ROOT / 'PROTOCOL.json').read_text())
    pinned = protocol['oneeval_commit']
    upstream = ['one_eval/utils/bench_table/bench_gallery.json',
                'one_eval/toolkits/dataflow_eval_tool.py', 'one-eval-skill/scripts/run_eval.py',
                'one-eval-skill/scripts/run_metrics.py', 'one-eval-skill/scripts/_common.py',
                'one-eval-skill/scripts/render_report.py', 'requirements.txt', 'uv.lock']
    source_receipts = []
    for path in upstream:
        raw = get('https://raw.githubusercontent.com/OpenDCAI/One-Eval/' + pinned + '/' + path)
        name = path.replace('/', '__') + '.gz'
        (OUT / name).write_bytes(gzip.compress(raw, mtime=0))
        source_receipts.append({'path': path, 'local_file': name, 'bytes': len(raw),
                                'sha256': hashlib.sha256(raw).hexdigest(),
                                'git_blob_sha': hashlib.sha1(('blob ' + str(len(raw)) + '\0').encode()+raw).hexdigest()})
    dispositions = []
    for item in protocol['panel']:
        try:
            disposition = capture_dataset(item)
        except Exception as error:
            disposition = {**item, 'status': 'acquisition_failed_or_gated',
                           'error_type': type(error).__name__, 'error': str(error)}
        dispositions.append(disposition)
        print(item['bench'], item['split'], disposition['status'], disposition.get('rows', ''), flush=True)
        (OUT / 'DATASET_DISPOSITIONS.json').write_text(json.dumps(dispositions, indent=2) + '\n')
    lock_raw = gzip.decompress((OUT / 'uv.lock.gz').read_bytes())
    lock = tomllib.loads(lock_raw.decode())
    packages = [x for x in lock['package'] if 'dataflow' in x['name'].lower()]
    package_sources = []
    for package in packages:
        wheel = next((x for x in package.get('wheels', []) if 'py3-none-any' in x['url']), None)
        if not wheel:
            package_sources.append({'name': package['name'], 'version': package.get('version'), 'status': 'no universal wheel in lock'})
            continue
        raw = get(wheel['url'])
        assert 'sha256:' + hashlib.sha256(raw).hexdigest() == wheel['hash']
        archive = zipfile.ZipFile(io.BytesIO(raw))
        matching = [name for name in archive.namelist() if name.endswith('.py') and
                    any(term in name.lower() for term in ('bench_answer_generator', 'unified_bench', 'bench_dataset_evaluator'))]
        saved = []
        for name in matching:
            data = archive.read(name)
            local = 'dataflow_wheel__' + name.replace('/', '__')
            (OUT / local).write_bytes(data)
            saved.append({'path': name, 'local_file': local, 'sha256': hashlib.sha256(data).hexdigest()})
        package_sources.append({'name': package['name'], 'version': package.get('version'),
                                'wheel_sha256': hashlib.sha256(raw).hexdigest(), 'files': saved})
    (OUT / 'DATAFLOW_LOCKED_SOURCE.json').write_text(json.dumps(package_sources, indent=2) + '\n')
    (OUT / 'UPSTREAM_SOURCE_RECEIPTS.json').write_text(json.dumps(source_receipts, indent=2) + '\n')
    (OUT / 'HTTP_ATTEMPTS.json').write_text(json.dumps(ATTEMPTS, indent=2) + '\n')
    print('Capture complete; no inference calls', flush=True)

if __name__ == '__main__':
    main()
