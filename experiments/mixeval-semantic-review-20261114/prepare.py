import hashlib, json, pathlib
BASE=pathlib.Path(__file__).resolve().parent
SRC=BASE.parent/'prior'/'real-generation'
def sha(b):return hashlib.sha256(b).hexdigest()
def jl(p):return [json.loads(x) for x in p.read_text().splitlines()]
manifest=jl(SRC/'manifest.jsonl');responses=jl(SRC/'responses.jsonl');caps=json.loads((SRC/'ANALYSIS_CAPTURES.json').read_text())
assert len(manifest)==len(responses)==len(caps)==80
assert len({x['trial_id'] for x in manifest})==80
byid={x['trial_id']:x for x in responses}; cap={x['trial_id']:x for x in caps}
sources={x['source_index']:x for x in json.loads((SRC/'selected20.json').read_text())}
packet=[];key=[]
for m in manifest:
 t=m['trial_id'];r=byid[t];c=cap[t]
 assert r['request_sha256']==m['request_sha256']
 assert sha(r['output_text'].encode())==r['output_text_sha256']
 oid=sha(('semantic-review-v1:'+t).encode())[:16]
 key.append({'opaque_id':oid,'trial_id':t,'model':c['model'],'condition':c['condition'],'source_index':m['source_index'],'judged':c['judged'],'common_rule_score':c['score']})
 if not c['judged']:continue
 s=sources[m['source_index']]['record']
 packet.append({'opaque_id':oid,'source_question':s['prompt'],'source_context':s['context'],'accepted_answers':s['target'],'response_text':r['output_text']})
packet.sort(key=lambda x:x['opaque_id']);key.sort(key=lambda x:x['opaque_id'])
assert len(packet)==69 and sum(not x['judged'] for x in key)==11
for name,rows in [('packet.jsonl',packet),('key.jsonl',key)]:
 (BASE/name).write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows))
receipt={'protocol_sha256':sha((BASE/'PROTOCOL.json').read_bytes()),'inputs':{n:sha((SRC/n).read_bytes()) for n in ['manifest.jsonl','responses.jsonl','selected20.json','ANALYSIS_CAPTURES.json']},'packet_sha256':sha((BASE/'packet.jsonl').read_bytes()),'key_sha256':sha((BASE/'key.jsonl').read_bytes()),'eligible':69,'unknown':11,'new_api_calls':0}
(BASE/'PREPARATION.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt))
