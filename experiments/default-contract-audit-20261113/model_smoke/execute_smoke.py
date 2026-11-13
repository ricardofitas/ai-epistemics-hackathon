"""Execute a fixed request list once, with explicit pacing and sanitized journals."""
import argparse
import base64
import datetime as dt
import gzip
import hashlib
import json
import os
from pathlib import Path
import time
import urllib.request

import run_adaption_stream_pilot as transport

ROOT=Path(__file__).resolve().parent

def preflight():
    protocol=json.loads((ROOT/'PROTOCOL.json').read_text())
    for name,pin in protocol['frozen_files'].items():
        raw=gzip.decompress(base64.b64decode((ROOT/(name+'.gz.b64')).read_text()))
        assert hashlib.sha256(raw).hexdigest()==pin
        p=ROOT/name
        if p.exists():assert p.read_bytes()==raw
        else:p.write_bytes(raw)
    rows,manifest_hash=transport.load_manifest(ROOT)
    assert len(rows)==96
    return protocol,rows,manifest_hash

def run():
    protocol,rows,manifest_hash=preflight()
    assert os.environ.get('GITHUB_RUN_ATTEMPT')=='1'
    assert os.environ.get('GITHUB_REF')=='refs/heads/ricardo/default-contract-model-smoke-20261113'
    assert not any((ROOT/name).exists() for name in ['api_artifacts','stream_journals','responses.jsonl'])
    credential=os.environ['ADAPTION_API_KEY']
    req=urllib.request.Request('https://api.prod.adaptionlabs.ai/api/v1/models?type=hosted',headers={'Authorization':'Bearer '+credential})
    with urllib.request.build_opener(transport.NoRedirect()).open(req,timeout=30) as response:catalogue=json.load(response)
    available={row.get('id') for row in catalogue.get('data',[]) if isinstance(row,dict)}
    (ROOT/'CATALOGUE_RECEIPT.json').write_text(json.dumps({'utc':transport.now(),'required':protocol['models'],'required_available':sorted(set(protocol['models'])&available)},indent=2)+'\n')
    assert set(protocol['models'])<=available,'Fixed solver unavailable; no model calls made'
    artifacts=ROOT/'api_artifacts';journals=ROOT/'stream_journals'
    artifacts.mkdir();journals.mkdir()
    results=[];last_start=None
    for row in rows:
        if last_start is not None:
            delay=max(0,5-(time.monotonic()-last_start))
            if delay:time.sleep(delay)
        last_start=time.monotonic()
        try:record=transport.run_trial(row,credential,120,artifacts,journals)
        except Exception as error:
            record={'trial_id':row['trial_id'],'attempt_count':1,'local_capture_error':type(error).__name__,'completed_nonempty':False}
            if not (artifacts/(row['trial_id']+'.json')).exists():transport.atomic_json(artifacts/(row['trial_id']+'.json'),record)
        results.append(record)
        print(json.dumps({'trial_id':row['trial_id'],'http_status':record.get('http_status'),'completed_nonempty':record.get('completed_nonempty')}),flush=True)
        if record.get('http_status')==429:time.sleep(60)
    (ROOT/'responses.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in results))
    (ROOT/'EXECUTION_RECEIPT.json').write_text(json.dumps({'utc':transport.now(),'run_id':os.environ['GITHUB_RUN_ID'],'execution_commit':os.environ['GITHUB_SHA'],'manifest_sha256':manifest_hash,'planned':len(rows),'recorded':len(results),'completed_nonempty':sum(bool(r.get('completed_nonempty')) for r in results),'attempts_per_request':1,'minimum_start_interval_seconds':5,'concurrency':1},indent=2)+'\n')

def finalize():
    secret=os.environ.get('ADAPTION_API_KEY','').encode()
    files=[p for p in ROOT.rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    safe=all(not secret or secret not in p.read_bytes() for p in files)
    with open(os.environ['GITHUB_OUTPUT'],'a') as stream:stream.write('safe='+str(safe).lower()+'\n')
    assert safe,'Credential scan failed'
    (ROOT/'ARTIFACT_INDEX.json').write_text(json.dumps({'credential_scan_passed':True,'files':[{'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(files)]},indent=2)+'\n')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['preflight','run','finalize']);args=parser.parse_args()
    if args.mode=='preflight':preflight()
    elif args.mode=='run':run()
    else:finalize()
