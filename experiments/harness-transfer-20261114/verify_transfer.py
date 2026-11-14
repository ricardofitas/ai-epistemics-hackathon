"""Verify captured native construction, selection and real local guard accounting."""
import json,gzip,hashlib
from pathlib import Path
from collections import Counter
ROOT=Path(__file__).resolve().parent;BASE=Path(__import__('sys').argv[1]).resolve()
def rows(p):return [json.loads(x) for x in gzip.decompress(p.read_bytes()).splitlines()]
def canonical(x):return json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()
inputs=rows(ROOT/'SELECTED_INPUTS.jsonl.gz');records=rows(ROOT/'REQUEST_CAPTURE.jsonl.gz')
assert len(inputs)==200 and len(records)==1000
key={(r['task'],r['source_index']):r for r in inputs};assert len(key)==200
for task,name in [('arc_challenge','arc-challenge'),('openbookqa','openbookqa')]:
 full=rows(BASE/'work/holdout/capture'/name/'SOURCE_ROWS.jsonl.gz')
 expected=sorted(range(len(full)),key=lambda i:(hashlib.sha256(b'harness-transfer-v1|'+canonical(full[i])).hexdigest(),i))[:100]
 assert expected==[r['source_index'] for r in inputs if r['task']==task]
 assert all(full[i]==key[(task,i)]['record'] for i in expected)
counts=Counter();request_count=0
for r in records:
 source=key[(r['task'],r['source_index'])]['record'];q=source.get('question',source.get('question_stem'));opts=source['choices']['text'];gold=list(map(str,source['choices']['label'])).index(str(source['answerKey']))
 assert r['source_target']==r['native_target']==gold
 rec=r['adapter_record'];actual=r['actual_requests'];condition=r['condition']
 assert rec['choices']==opts and rec['source_choices']==opts and rec['correct_text']==opts[gold]
 assert rec['reference']==chr(65+gold) and rec['source_question']==q and q in rec['prompt']
 if condition in ['native','benign_context_spacing']:
  assert len(actual)==len(opts) and [x['idx'] for x in actual]==list(range(len(opts)))
  assert [x['continuation'] for x in actual]==[' '+x for x in opts]
  assert all(x['context']==rec['prompt'] and q in x['context'] for x in actual)
  assert r['v2']['status']==r['wire']['status']=='PASS' and r['constructed_backend_calls']==1
  if condition=='native':request_count+=len(actual)
  counts['native_or_benign_pass']+=1
 else:
  if condition=='drop_continuation':assert len(actual)==len(opts)-1
  elif condition=='replace_continuation':assert [x['continuation'] for x in actual]!=[' '+x for x in opts]
  else:assert all(q not in x['context'] for x in actual)
  assert r['v2']['status']=='PASS' and r['wire']['status']=='FAIL' and r['constructed_backend_calls']==0
  counts['controlled_stale_metadata_rejected_at_wire']+=1
initial=json.loads((ROOT/'INITIAL_DECISION_ONLY_RESULTS.json').read_text());final=json.loads((ROOT/'RESULTS.json').read_text())
assert initial==final and not final['exceptions']
result=dict(status='PASS',source_units=200,native_condition_rows=200,native_per_option_request_objects=request_count,condition_records=1000,counts=dict(counts),actual_local_backend_invocations=sum(r['constructed_backend_calls'] for r in records),provider_model_calls=0,pre_and_post_instrumentation_decisions_identical=True,scope='Exact native method projection; same known source corpus, newly sampled engine request outputs. Full engine/model execution is not claimed.')
(ROOT/'VERIFICATION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))

