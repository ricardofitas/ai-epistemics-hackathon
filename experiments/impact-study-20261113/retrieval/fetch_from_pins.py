#!/usr/bin/env python3
"""Verify or restore the exact public source bytes; never calculate effectiveness."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import gzip
import hashlib
import json
from pathlib import Path
import urllib.parse
import urllib.request


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def check_record(directory, record, fetch):
    name = record['local_file']
    if Path(name).name != name:
        raise ValueError('Unsafe source filename')
    target = directory / name
    downloaded = 0
    if not target.exists():
        if not fetch:
            raise FileNotFoundError(name)
        url = urllib.parse.urlsplit(record['url'])
        if url.scheme != 'https' or url.hostname != 'ir.nist.gov':
            raise ValueError('Source is not the pinned official HTTPS host')
        request = urllib.request.Request(record['url'], headers={'User-Agent':'Mozilla/5.0'})
        with urllib.request.urlopen(request, timeout=60) as response:
            raw = response.read(record['bytes'] + 1)
        if len(raw) != record['bytes'] or sha(raw) != record['sha256']:
            raise ValueError('Downloaded source differs from exact pinned bytes: ' + name)
        target.write_bytes(raw)
        downloaded = len(raw)
    raw = target.read_bytes()
    if len(raw) != record['bytes'] or sha(raw) != record['sha256']:
        raise ValueError('Cached source differs from exact pin: ' + name)
    if 'uncompressed_sha256' in record:
        plain = gzip.decompress(raw)
        if len(plain) != record['uncompressed_bytes'] or sha(plain) != record['uncompressed_sha256']:
            raise ValueError('Decompressed source differs from exact pin: ' + name)
    return {'name':name, 'verified':True, 'downloaded_bytes':downloaded}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory',type=Path,default=Path(__file__).resolve().parent)
    parser.add_argument('--fetch-missing',action='store_true')
    parser.add_argument('--byte-budget',type=int,default=100_000_000)
    args=parser.parse_args()
    source=args.directory/'source'
    receipt=json.loads((source/'download_receipt.json').read_text())
    records=receipt['records']
    if len(records)!=127 or any('error_type' in r for r in records):
        raise ValueError('This exact source restoration expects the frozen successful127record receipt')
    missing=[r for r in records if not (source/r['local_file']).exists()]
    if args.fetch_missing and sum(r['bytes']+1 for r in missing)>args.byte_budget:
        raise ValueError('Reserved download budget exceeds bound')
    with ThreadPoolExecutor(max_workers=4) as pool:
        results=list(pool.map(lambda r:check_record(source,r,args.fetch_missing),records))
    print(json.dumps({'sources_verified':len(results),'downloaded_bytes':sum(r['downloaded_bytes'] for r in results),'performance_computed':False}))


if __name__=='__main__':
    main()
