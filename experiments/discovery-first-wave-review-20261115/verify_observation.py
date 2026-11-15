"""Read-only validation of frozen designs and first provider wave; no network or dispatch."""
from pathlib import Path
import json,hashlib,collections,gzip,tarfile,base64,io,zipfile
R=Path(__file__).parent
C=lambda x:json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode();H=lambda x:hashlib.sha256(x).hexdigest()
info={}
for study,aid,wid,mhash,count,cap in [('wino','14143821883','14143324169','b7374835790f312c2730a959079e379f6eb81006dc9cdaba361acd295fa077c8',1024,30),('siqa','14144275362','14143559450','1a0b6f7bf7eefa5ef6240289191df0295e5214b098403c0879cf3ebc69abe131',3200,70)]:
 p=R/(aid+'_payload')/('confirmatory_'+study)/'manifest.jsonl';assert H(p.read_bytes())==mhash;rows=[json.loads(x) for x in p.read_bytes().splitlines()];idx={r['trial_id']:r for r in rows};assert len(rows)==len(idx)==count;models=collections.Counter(r['request_payload']['model'] for r in rows);assert len(models)==4 and set(models.values())=={count//4}
 for r in rows:assert H(C(r['request_payload']))==r['request_sha256'];assert r['request_payload']['max_tokens']==8192
 w=R/(wid+'_wave');progress=json.load(open(w/'progress.json'));queue=json.load(open(w/'queue_plan.json'));assert progress['cap_credits']==cap;assert progress['new_post_cutoff_utc']=='2026-11-15T10:15:00Z';assert queue['manifest_pins'][0]['sha256']==mhash
 intents=[json.loads(x) for x in (w/'intent.jsonl').read_bytes().splitlines()];keys=set()
 for r in intents:
  key=r['trial_id'],r['attempt'];assert key not in keys;keys.add(key);assert r['request_sha256']==idx[r['trial_id']]['request_sha256'];assert r['at']<'2026-11-15T10:15:00Z'
 attempts=[json.loads(x) for x in (w/'attempts.jsonl').read_bytes().splitlines()] if (w/'attempts.jsonl').exists() else [];complete=0
 for r in attempts:
  req=idx[r['trial_id']];assert r['request_payload']==req['request_payload'];assert r['request_sha256']==req['request_sha256'];assert (r['trial_id'],r['attempt']) in keys
  if r.get('eligible'):
   assert r['http_status']==200 and r['returned_model']==req['request_payload']['model'] and r['response_id'];assert r['status']=='stop';assert not r['stream_incomplete'];assert r['text'];u=r['usage'];assert type(u['prompt_tokens'])==int and type(u['completion_tokens'])==int and 0<=u['completion_tokens']<=8192;assert r['output_text_sha256']==H(r['text'].encode());complete+=1
  path=w/'responses'/f"{r['trial_id']}-{r['attempt']}.json.gz"
  if path.exists():raw=json.loads(gzip.decompress(path.read_bytes()));assert raw==r
 assert complete==progress['complete'];assert len({r['trial_id'] for r in attempts})==progress['recorded_unique']
 info[study]={'study_planned':count,'manifest_sha256':mhash,'models':dict(models),'snapshot_utc':progress['at'],'artifact':int(wid),'unique_intents':len({r['trial_id'] for r in intents}),'terminal_attempts':len(attempts),'complete_verified':complete,'inflight_snapshot':progress['active'],'pending_snapshot':progress['pending'],'complete_adjacent_arm_pairs_snapshot':progress['complete_causal_response_pairs'],'cap_credits':cap,'executor_spent_or_committed_credits':progress['spent_or_committed_credits'],'scope':'Actual terminal evidence only. Frozen pre-inference RESULTS with0responses is not a measured study result; intents are not verified provider completions.'}
(R/'OBSERVATION_VERIFICATION.json').write_text(json.dumps({'status':'PASS_READ_ONLY_FROZEN_MANIFEST_AND_INITIAL_RESPONSE_IDENTITY','studies':info,'new_calls_by_observer':0,'manuscript_changes':0,'credential_changes':0,'scientific_results_inferred_from_initial_snapshot':False},indent=2)+'\n');print(info)
