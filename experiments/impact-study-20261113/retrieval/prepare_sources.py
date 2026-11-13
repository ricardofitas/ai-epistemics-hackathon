#!/usr/bin/env python3
"""Prepare an outcome-blind official Round5 run registry and fetch exact bytes.
No evaluation report, qrel joining, metric, significance test, or score ranking is read.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import datetime as dt
import gzip
import hashlib
import html
import json
from pathlib import Path
import re
import urllib.request
import urllib.parse

BASE = 'https://ir.nist.gov/trec-covid/archive/archive-round5.html'
QRELS = 'https://ir.nist.gov/trec-covid/data/qrels-covid_d5_j4.5-5.txt'
HEADERS = {'User-Agent': 'Mozilla/5.0', 'Accept': '*/*'}
SAFE_HEADERS = ['Content-Type', 'Content-Length', 'ETag', 'Last-Modified', 'Date']

def sha(raw): return hashlib.sha256(raw).hexdigest()
def stamp(): return dt.datetime.now(dt.timezone.utc).isoformat()
def save(path, value): path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')

def request(url, method='GET'):
    req = urllib.request.Request(url, headers=HEADERS, method=method)
    with urllib.request.urlopen(req, timeout=60) as res:
        headers = {k:res.headers.get(k) for k in SAFE_HEADERS if res.headers.get(k)}
        return res.status, headers, res.read() if method == 'GET' else b''

def registry(raw):
    text = raw.decode('utf-8')
    candidates = []
    for match in re.finditer(r'<li>([^<\r\n]+)\s*<ul>(.*?)</ul>', text, re.S | re.I):
        team = html.unescape(match.group(1).strip())
        for link, name in re.findall(r'<a\s+href="([^"]+\.gz)">([^<]+)\s+submission file</a>', match.group(2), re.I):
            name = html.unescape(name.strip())
            candidates.append({'run_tag': name, 'team': team,
                               'url': urllib.parse.urljoin(BASE, link)})
    candidates.sort(key=lambda r:r['run_tag'])
    if len(candidates) != 126 or len({r['run_tag'] for r in candidates}) !=126:
        raise ValueError('Official126run registry changed or parser did not capture it')
    return candidates

def head_one(row):
    try:
        status, headers, _ = request(row['url'], 'HEAD')
        return {'run_tag':row['run_tag'], 'status':status, 'headers':headers}
    except Exception as exc:
        return {'run_tag':row['run_tag'], 'error_type':type(exc).__name__, 'error':str(exc)}

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--directory',type=Path,default=Path(__file__).resolve().parent)
    ap.add_argument('--prepare',action='store_true')
    ap.add_argument('--head',action='store_true')
    ap.add_argument('--fetch',action='store_true')
    ap.add_argument('--frozen-registry-sha256')
    ap.add_argument('--byte-budget',type=int,default=100_000_000)
    args=ap.parse_args(); root=args.directory;root.mkdir(parents=True,exist_ok=True)
    if args.prepare:
        path=root/'candidate_registry.json'
        if path.exists():raise ValueError('Refusing to replace frozen-intent registry')
        index=root/'archive-round5.html'
        if not index.exists():
            status,headers,raw=request(BASE); index.write_bytes(raw)
            save(root/'archive_index_receipt.json',{'fetched_utc':stamp(),'url':BASE,'http_status':status,'headers':headers,'sha256':sha(raw),'bytes':len(raw)})
        rows=registry(index.read_bytes())
        out={'created_utc':stamp(),'status':'eligibility_prepared_before_candidate_performance_inspection',
             'source_index_url':BASE,'source_index_sha256':sha(index.read_bytes()),
             'selection':'All126submission-file links in official Round5 archive, sortedrun_tag; no score reports/rankings accessed for this registry.',
             'eligibility':'All126plannedruns are retained. Missingtopics and shortrankings receive canonicalzero/padding behavior; wholly unavailable/malformedsources are operationallymissing, not inventedzeros. No substitutions.',
             'candidate_count':len(rows),'topic_ids':list(range(1,51)),
             'ranking':'Score descending; trec_eval-compatible tie convention must be independently pinned before metrics. Do not use row rank as authoritative score ordering.',
             'matching_qrels':QRELS,'candidate_scope':'Official residual Round5 task; do not substitute BEIR/Complete cumulative qrels.',
             'performance_inspected':False,'candidates':rows}
        save(path,out)
        print(json.dumps({'prepared_candidates':len(rows),'registry_sha256':sha(path.read_bytes())}))
    path=root/'candidate_registry.json'; reg=json.loads(path.read_text())
    if args.head:
        results=[]
        with ThreadPoolExecutor(max_workers=4) as pool:
            for fut in as_completed([pool.submit(head_one,r) for r in reg['candidates']]):results.append(fut.result())
        results.sort(key=lambda r:r['run_tag'])
        known=[int(r['headers']['Content-Length']) for r in results if r.get('status')==200 and r.get('headers',{}).get('Content-Length')]
        out={'checked_utc':stamp(),'method':'HEAD only; no run/qrel metric computation','candidates':len(results),'successful':sum(r.get('status')==200 for r in results),'sizes_known':len(known),'compressed_bytes_known':sum(known),'byte_budget':args.byte_budget,'pool_not_modified':True,'records':results}
        save(root/'head_availability.json',out)
        print(json.dumps({k:v for k,v in out.items() if k!='records'}))
    if args.fetch:
        if args.frozen_registry_sha256!=sha(path.read_bytes()):raise ValueError('External exact registry hash required before run fetching')
        target=root/'source';target.mkdir(exist_ok=True)
        if (target/'download_receipt.json').exists():raise ValueError('Refusing duplicate fetch batch')
        head_path=root/'head_availability.json'
        head=json.loads(head_path.read_text())
        sizes={r['run_tag']:int(r['headers']['Content-Length']) for r in head['records']}
        sources=[{'run_tag':'MATCHING_QRELS','url':reg['matching_qrels']}]+reg['candidates']
        reservations={row['run_tag']:(2_000_000 if row['run_tag']=='MATCHING_QRELS' else sizes[row['run_tag']]+1) for row in sources}
        if sum(reservations.values())>args.byte_budget:raise ValueError('Reserved source bytebudget exceeds bound before fetching')
        def fetch_one(row):
            tag=row['run_tag']; limit=reservations[tag]
            record={'run_tag':tag,'url':row['url'],'reserved_bytes':limit}
            try:
                req=urllib.request.Request(row['url'],headers=HEADERS)
                with urllib.request.urlopen(req,timeout=60) as res:
                    raw=res.read(limit)
                    record.update({'http_status':res.status,'headers':{k:res.headers.get(k) for k in SAFE_HEADERS if res.headers.get(k)},'bytes':len(raw),'sha256':sha(raw)})
                if len(raw)>=limit:raise ValueError('Response reached reservedbyte limit; no silently truncatedvalid source')
                name='qrels-covid_d5_j4.5-5.txt' if tag=='MATCHING_QRELS' else tag+'.gz'
                (target/name).write_bytes(raw);record['local_file']=name
                if name.endswith('.gz'):
                    uncompressed=gzip.decompress(raw)
                    # Structural metadata only; no retrieval effectiveness is computed.
                    rows=[line.split() for line in uncompressed.decode().splitlines() if line.strip()]
                    topics=sorted({int(r[0]) for r in rows})
                    record.update({'uncompressed_bytes':len(uncompressed),'uncompressed_sha256':sha(uncompressed),'row_count':len(rows),'topic_ids':topics,'all_six_columns':all(len(r)==6 for r in rows)})
                else:record['row_count']=len(raw.splitlines())
            except Exception as exc:
                record.update({'error_type':type(exc).__name__,'error':str(exc)})
            return record
        records=[]
        with ThreadPoolExecutor(max_workers=4) as pool:
            for future in as_completed([pool.submit(fetch_one,row) for row in sources]):
                rec=future.result();records.append(rec)
                # Progress is source availability only, never model or retrieval scores.
                print(json.dumps({'source_records':len(records),'last_tag':rec['run_tag'],'bytes':rec.get('bytes'),'error':rec.get('error_type')}),flush=True)
        records.sort(key=lambda r:r['run_tag'])
        used=sum(r.get('bytes',0) for r in records)
        save(target/'download_receipt.json',{'fetched_utc':stamp(),'registry_sha256':sha(path.read_bytes()),'bytes_downloaded':used,'performance_computed':False,'records':records})
        print(json.dumps({'sources':len(records),'bytes':used,'performance_computed':False}))

if __name__=='__main__':main()
