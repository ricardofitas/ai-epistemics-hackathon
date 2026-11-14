"""Independent source/capture/dispatch reconciliation; no native engine or model rerun."""
import json,gzip,hashlib
from pathlib import Path
from collections import Counter
P=Path(__file__).resolve().parent
canon=lambda v:json.dumps(v,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()
hashv=lambda v:hashlib.sha256(canon(v)).hexdigest()
rows=lambda p:[json.loads(x) for x in gzip.decompress(p.read_bytes()).splitlines()]
proto=json.loads((P/'PROTOCOL.json').read_text());source=rows(P/'input/SELECTED_INPUTS.jsonl.gz');registry={s['task']+':'+str(s['source_index']):s for s in source};assert len(registry)==200
for s in source:assert hashv(s['record'])==s['source_sha256']
records=rows(P/'RESULTS.jsonl.gz');assert len(records)==1600;seen=set();totals=Counter();calls=0;option_count=0;cases=Counter()
for r in records:
 key=r['source_key'];condition=r['condition'];assert key in registry and (key,condition) not in seen;seen.add((key,condition));s=registry[key];raw=s['record'];gold=list(map(str,raw['choices']['label'])).index(str(raw['answerKey']));question=raw.get('question',raw.get('question_stem'));options=raw['choices']['text'];carrier=r['carrier'];observed=r['report']['status'];assert observed==proto['conditions'][condition];totals[observed]+=1;cases[condition]+=1
 primitive=[(a['request_type'],int(a['doc_id']),int(a['idx']),a['context'],a['continuation']) for a in carrier];assert hashv(primitive)==r['report']['snapshot_sha256']
 assert r['report']['option_requests']==len(carrier)
 if observed=='PASS':
  assert len(r['sink_calls'])==1 and r['sink_calls'][0]['snapshot_sha256']==hashv(primitive)
  assert r['sink_calls'][0]['option_requests']==len(options)
  assert [a['idx'] for a in carrier]==list(range(len(options)))
  assert [a['continuation'] for a in carrier]==[' '+s for s in options]
  assert all(question.strip() in a['context'] and a['request_type']=='loglikelihood' for a in carrier)
  assert r['reference']==gold and all(x==s['source_sha256'] for x in r['native_documents_sha256'])
  calls+=1;option_count+=len(carrier)
 else:assert r['sink_calls']==[] and r['report']['failures']
 if condition=='drop_continuation':assert len(carrier)==len(options)-1
 if condition=='replace_continuation':assert any(a['continuation'].startswith(' REPLACED_CONTINUATION_') for a in carrier)
 if condition=='omit_question':assert all(question not in a['context'] for a in carrier)
 if condition=='wrong_reference':assert r['reference']!=gold
 if condition=='substitute_document':assert all(x!=s['source_sha256'] for x in r['native_documents_sha256'])
 if condition=='missing_trusted_source':assert r['report']['failures']==['trusted_source_unavailable']
assert set(seen)=={(k,c) for k in registry for c in proto['conditions']}
assert totals=={'PASS':400,'FAIL':1000,'INCOMPLETE':200} and calls==400 and option_count==1602
summary=json.loads((P/'SUMMARY.json').read_text());assert summary['statuses']==dict(totals) and summary['counting_sink_invocations']==calls and summary['dispatched_option_requests']==option_count and summary['native_option_requests']==801 and summary['errors']==[]
for n,want in proto['input_files_sha256'].items():assert hashlib.sha256((P/n).read_bytes()).hexdigest()==want
assert hashlib.sha256((P/'native_source_gate.py').read_bytes()).hexdigest()==proto['gate_sha256']
rt=json.loads((P/'RUNTIME_PROVENANCE.json').read_text());prior=json.loads((P/'input/NATIVE_INSTALL_PROVENANCE.json').read_text());assert rt['native_module_sha256']==prior['native_source_sha256'] and rt['dependencies']==prior['dependencies']
result=dict(status='PASS',source_units=200,condition_records=1600,statuses=dict(totals),counting_sink_invocations=400,failed_or_incomplete_sink_calls=0,accepted_request_snapshots_identical_at_sink=400,accepted_option_requests=1602,installed_native_module_hashes_verified=6,provider_model_requests=0,scope='Offline source/capture/gate reconciliation. No model/backend/tokenizer transport verified.')
(P/'VERIFICATION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
