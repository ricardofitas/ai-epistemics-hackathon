#!/usr/bin/env python3
"""Operational reconciliation of originals 1..4; no new scientific replication."""
import collections, decimal, hashlib, json, pathlib
R=pathlib.Path(__file__).resolve().parents[1]; O=pathlib.Path(__file__).resolve().parent
D=decimal.Decimal; all_attempts=[]; keys=set(); ids=set(); waves=[]; failures=[]
def check(x,msg):
    if not x:failures.append(msg)
for w in range(1,5):
    attempts=[]; final={}; zipfile=R/f'artifacts/wave{w}.zip'
    for section in ['front','back']:
        p=R/f'artifacts/wave{w}/s{w-1}-{section}/attempts.jsonl'
        aa=[json.loads(x) for x in p.read_text().splitlines() if x.strip()]
        for a in aa:
            check(25*(w-1)<=a['case']<25*w,f'wave{w}: case outside assigned range')
            if a['key'] in final:check(final[a['key']]['http']==429,f'wave{w}: retry after non429')
            final[a['key']]=a
            if a.get('response_id'):
                check(a['response_id'] not in ids,'duplicate response_id across originals');ids.add(a['response_id'])
        attempts+=aa
    check(not (keys&final.keys()),'duplicate slot across original waves');keys.update(final)
    check(len(final)==400,f'wave{w}: unique slots !=400')
    waves.append(dict(wave=w,zip_sha256=hashlib.sha256(zipfile.read_bytes()).hexdigest(),unique_slots=len(final),attempts=len(attempts),eligible=sum(a.get('eligible') is True for a in final.values()),status=dict(collections.Counter(a['status'] for a in final.values())),explicit_429=sum(a['http']==429 for a in attempts)))
    all_attempts+=attempts
prodpath=R/'code/results/summary.json';prodbytes=prodpath.read_bytes();prod=json.loads(prodbytes)
totals=dict(started_unique=len(keys),attempts=len(all_attempts),eligible=sum(w['eligible'] for w in waves),status=dict(sum((collections.Counter(w['status']) for w in waves),collections.Counter())),explicit_429=sum(w['explicit_429'] for w in waves),input_tokens=sum(a.get('usage',{}).get('input_tokens',0) for a in all_attempts),output_tokens=sum(a.get('usage',{}).get('output_tokens',0) for a in all_attempts),reported_cost=float(sum((D(str(a.get('usage',{}).get('cost',0))) for a in all_attempts),D(0))))
rates={'gemma-4-31b-it':(D('.09'),D('.34')),'qwen3.8-27b':(D('.039'),D('1.25')),'deepseek-v4-flash':(D('.045'),D('.14')),'glm-5.2':(D('1.40'),D('4.40'))}
rate_cost=sum(((D(a.get('usage',{}).get('input_tokens',0))*rates[a['model']][0]+D(a.get('usage',{}).get('output_tokens',0))*rates[a['model']][1])/D(1000000) for a in all_attempts),D(0))
check(abs(D(str(prod['rate_card_credits_without_cached_discount']))-rate_cost)<=D('.000000051'),'cumulative rate-card cost mismatch')
for k,v in totals.items():check(abs(prod[k]-v)<1e-10 if isinstance(v,float) else prod[k]==v,'production cumulative mismatch: '+k)
check(prod['planned']==3200 and prod['unstarted']==1600,'planned or pending count mismatch')
out=dict(scope='Operational four-original reconciliation only. Previous wave1..3 scientific verification is not counted again.',waves=waves,totals=totals,rate_card_cost_decimal=str(rate_cost),production_summary_sha256=hashlib.sha256(prodbytes).hexdigest(),pending_waves=[5,6,7,8],pending_source_indexes=[100,199],pending_slots=1600,failures=failures)
(O/'checkpoint_four_originals.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2));raise SystemExit(bool(failures))
