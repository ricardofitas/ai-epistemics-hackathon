"""Capture the four public source splits and freeze the prespecified SHA sample."""
import base64
import gzip
import hashlib
import io
import json
from pathlib import Path
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parent
HTTP_ATTEMPTS = []


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode()


def get(url):
    for attempt in range(1, 4):
        try:
            request = urllib.request.Request(url, headers={'User-Agent':'prospective-evaluation-contract-audit/1.0'})
            with urllib.request.urlopen(request, timeout=90) as response:
                data = response.read(80_000_001)
                assert len(data) <= 80_000_000
                HTTP_ATTEMPTS.append(dict(url=url, attempt=attempt, status=response.status, bytes=len(data)))
                return data
        except urllib.error.HTTPError as error:
            HTTP_ATTEMPTS.append(dict(url=url, attempt=attempt, status=error.code))
            if error.code not in (429, 500, 502, 503, 504) or attempt == 3:
                raise
            time.sleep(2 * attempt)


def unpack_support(protocol):
    data = base64.b64decode((ROOT / 'source_support.zip.b64').read_bytes())
    assert hashlib.sha256(data).hexdigest() == protocol['source_support_sha256']
    archive = ROOT / 'source_support.zip'
    archive.write_bytes(data)
    with zipfile.ZipFile(archive) as bundle:
        for name in bundle.namelist():
            assert not Path(name).is_absolute() and '..' not in Path(name).parts
        bundle.extractall(ROOT.parent)
    checker = ROOT.parent / 'oneeval_contract_checker_20261114/check_contract.py'
    assert hashlib.sha256(checker.read_bytes()).hexdigest() == protocol['checker_sha256']


def metadata(repository, revision):
    url = 'https://huggingface.co/api/datasets/' + repository + '/revision/' + urllib.parse.quote(revision, safe='')
    return json.loads(get(url))


def capture(entry, protocol):
    import pyarrow.parquet as pq
    name = entry['bench_name']
    repository = entry['meta']['hf_meta']['hf_repo']
    settings = entry['meta']['download_config']
    config, split = settings['config'], settings['split']
    output = ROOT / 'capture' / name
    output.mkdir(parents=True, exist_ok=True)
    current = metadata(repository, 'main')
    index = json.loads(get('https://huggingface.co/api/datasets/' + repository + '/parquet/' + urllib.parse.quote(config, safe='') + '/' + split))
    assert isinstance(index, list) and index
    converted = metadata(repository, 'refs/convert/parquet')
    rows, files = [], []
    for number, url in enumerate(index):
        url = url.replace('/resolve/refs%2Fconvert%2Fparquet/', '/resolve/' + converted['sha'] + '/')
        url = url.replace('/resolve/refs/convert/parquet/', '/resolve/' + converted['sha'] + '/')
        raw = get(url)
        path = output / ('part-' + str(number) + '.parquet')
        path.write_bytes(raw)
        rows.extend(pq.read_table(io.BytesIO(raw)).to_pylist())
        files.append(dict(file=path.name, url=url, bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest()))
    raw_lines = b''.join(canonical(row) + b'\n' for row in rows)
    (output / 'SOURCE_ROWS.jsonl.gz').write_bytes(gzip.compress(raw_lines, mtime=0))
    order = sorted(range(len(rows)), key=lambda i:(hashlib.sha256(canonical(rows[i])).hexdigest(), i))
    selected = order[:protocol['maximum_sample_rows']]
    selection = [dict(source_index=i, source_sha256=hashlib.sha256(canonical(rows[i])).hexdigest(), record=rows[i]) for i in selected]
    payload = b''.join(canonical(row) + b'\n' for row in selection)
    (output / 'SELECTED.jsonl.gz').write_bytes(gzip.compress(payload, mtime=0))
    try:
        card = get('https://huggingface.co/datasets/' + repository + '/resolve/' + current['sha'] + '/README.md')
        (output / 'SOURCE_CARD.md').write_bytes(card)
    except urllib.error.HTTPError:
        pass
    return dict(benchmark=name, status='captured', repository=repository, config=config, split=split,
                main_revision=current['sha'], converted_revision=converted['sha'], total_source_rows=len(rows),
                selected_rows=len(selection), source_rows_sha256=hashlib.sha256(raw_lines).hexdigest(),
                selected_rows_sha256=hashlib.sha256(payload).hexdigest(), parquet_files=files)


def main():
    protocol = json.loads((ROOT / 'PROTOCOL.json').read_text())
    assert hashlib.sha256((ROOT / 'GALLERY.json').read_bytes()).hexdigest() == protocol['gallery_sha256']
    unpack_support(protocol)
    entries = json.loads((ROOT / 'GALLERY.json').read_text())['benches']
    results = []
    for entry in entries:
        try:
            result = capture(entry, protocol)
        except Exception as error:
            result = dict(benchmark=entry['bench_name'], status='acquisition_failed', error_type=type(error).__name__, error=str(error))
        results.append(result)
        (ROOT / 'DISPOSITIONS.json').write_text(json.dumps(results, indent=2) + '\n')
        (ROOT / 'HTTP_ATTEMPTS.json').write_text(json.dumps(HTTP_ATTEMPTS, indent=2) + '\n')
        print(json.dumps({k:v for k,v in result.items() if k in ['benchmark','status','selected_rows','total_source_rows','error_type']}), flush=True)
    print('Public-source capture complete. Model requests: 0.', flush=True)


if __name__ == '__main__':
    main()
