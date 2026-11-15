"""Offline authentication and unknown/retry accounting; no semantic adjudication."""
from pathlib import Path
import json,hashlib,collections,gzip,zipfile,base64,tarfile,io
R=Path(__file__).parent
H=lambda b:hashlib.sha256(b).hexdigest()
C=lambda x:json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()
PINS={'14144275362':'23ebd3b5cf2238182995813e14b54622494493f93f8d6d36352c75c3c426445f','14147989989':'b23f7ef53290ba95fc1a56271fb2f8be7612d4662a32440a787ca2d839943dcd'}
for aid,pin in PINS.items():
 p=R/(aid+'.zip');assert H(p.read_bytes())==pin
 with zipfile.ZipFile(p) as z:
  assert z.testzip() is None
  assert all(not Path(n).is_absolute() and '..' not in Path(n).parts for n in z.namelist());z.extractall(R/aid)
 if aid=='14144275362':
  raw=base64.b64decode(''.join(p.read_text() for p in sorted((R/aid).glob('payload-*.b64'))),validate=True);assert H(raw)==json.load(open(R/aid/'PAYLOAD_RECEIPT.json'))['payload_sha256']
  with tarfile.open(fileobj=io.BytesIO(raw),mode='r:*') as t:
   assert all(not Path(m.name).is_absolute() and '..' not in Path(m.name).parts and not m.issym() and not m.islnk() for m in t.getmembers());t.extractall(R/(aid+'_payload'),filter='data')
 else:
  for p in (R/aid).glob('*.zip'):
   with zipfile.ZipFile(p) as z:
    assert z.testzip() is None;assert all(not Path(n).is_absolute() and '..' not in Path(n).parts for n in z.namelist());z.extractall(R/(aid+'_wave'))
p=R/'14144275362_payload/confirmatory_siqa/manifest.jsonl';mh='1a0b6f7bf7eefa5ef6240289191df0295e5214b098403c0879cf3ebc69abe131';assert H(p.read_bytes())==mh
planned=[json.loads(l) for l in p.read_text().splitlines()];idx={r['trial_id']:r for r in planned};assert len(idx)==len(planned)==3200
assert set(collections.Counter(r['request_payload']['model'] for r in planned).values())=={800}
for r in planned:assert H(C(r['request_payload']))==r['request_sha256'];assert r['request_payload']['max_tokens']==8192
w=R/'14147989989_wave';progress=json.load(open(w/'progress.json'));intents=[json.loads(l) for l in (w/'intent.jsonl').read_text().splitlines()];attempts=[json.loads(l) for l in (w/'attempts.jsonl').read_text().splitlines()]
intentkeys=set()
for r in intents:
 k=(r['trial_id'],r['attempt']);assert k not in intentkeys;intentkeys.add(k);assert r['request_sha256']==idx[r['trial_id']]['request_sha256'];assert r['at']<'2026-11-15T10:15:00Z'
groups=collections.defaultdict(list);by_model=collections.defaultdict(collections.Counter);response_ids=[];eligible=0;usage=collections.Counter()
for r in attempts:
 k=(r['trial_id'],r['attempt']);assert k in intentkeys;req=idx[r['trial_id']];assert r['request_payload']==req['request_payload'];assert r['request_sha256']==req['request_sha256'];groups[r['trial_id']].append(r)
 raw=w/'responses'/f"{r['trial_id']}-{r['attempt']}.json.gz";assert raw.exists();assert json.loads(gzip.decompress(raw.read_bytes()))==r
 by_model[r['model']][str(r['http_status'])]+=1
 if r.get('response_id'):response_ids.append(r['response_id'])
 if r['http_status']==200:
  assert r['returned_model']==req['request_payload']['model'];assert r['response_id'];assert r['usage_valid'];u=r['usage'];assert type(u['prompt_tokens'])==int and type(u['completion_tokens'])==int and 0<=u['completion_tokens']<=8192
  for name in ['prompt_tokens','completion_tokens']:usage[name]+=u[name]
 if r.get('eligible'):
  assert r['http_status']==200 and r['status']=='stop' and not r['stream_incomplete'] and r['text'];assert H(r['text'].encode())==r['output_text_sha256'];eligible+=1;by_model[r['model']]['eligible']+=1
 elif r['http_status']==429:by_model[r['model']]['explicit429_rejected_attempt']+=1
 else:by_model[r['model']]['unknown_final']+=1
assert len(response_ids)==len(set(response_ids))
for g in groups.values():
 assert len({r['attempt'] for r in g})==len(g)
 for r in sorted(g,key=lambda x:x['attempt'])[:-1]:assert r['http_status']==429,'Ambiguous/empty/504 resent'
assert progress['complete']==eligible;assert progress['recorded_unique']==len(groups);assert progress['unique_started']==len({r['trial_id'] for r in intents});assert len(intents)-len(attempts)==progress['active']
assert progress['planned']==3200 and progress['cap_credits']==70 and progress['new_post_cutoff_utc']=='2026-11-15T10:15:00Z'
analysis=json.load(open(w/'analysis/RESULTS.json'));assert analysis['semantic_labels_supplied']==0;assert analysis['complete_native_pairs']==progress['complete_causal_response_pairs']
result={'status':'PASS_AUTHENTICATED_SIQA_SNAPSHOT_NO_SEMANTIC_LABELS','artifact_id':14147989989,'sha256':PINS['14147989989'],'manifest_sha256':mh,'progress':progress,'intents':len(intents),'attempt_records_and_matching_raw_captures':len(attempts),'distinct_provider_response_ids':len(response_ids),'by_model':dict(by_model),'terminal_http504':sum(r['http_status']==504 for r in attempts),'terminal_200_length_unknown':sum(r['http_status']==200 and r['status']=='length' for r in attempts),'terminal_200_empty_stop_unknown':sum(r['http_status']==200 and r['status']=='stop' and not r['text'] for r in attempts),'only_prior429_repeated':True,'usage_returned_200_including_unknowns':dict(usage),'semantic_labels_in_runtime_artifact':0,'human_annotations_by_observer':0,'observer_model_calls':0,'semantic_review_owner':'Direct research execution worker; this observer assigns no labels','limits':'Native response-pair coverage is not semantic coverage. Cost commitment is not final billing or confirmed currency.'}
(R/'VERIFICATION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
