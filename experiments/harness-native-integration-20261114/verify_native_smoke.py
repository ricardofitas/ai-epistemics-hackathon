"""Independently reconcile installed-driver carriers and constructed scoring results."""
import json,gzip,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parent
PRIOR=Path(__import__('sys').argv[1]).resolve()
def rows(p):return [json.loads(x) for x in gzip.decompress(p.read_bytes()).splitlines()]
def canonical(x):return json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()
summary=json.loads((ROOT/'SUMMARY.json').read_text());assert summary['status']=='completed' and summary['errors']==[]
inputs=rows(PRIOR/'SELECTED_INPUTS.jsonl.gz');assert len(inputs)==200
source={(x['task'],x['source_index']):x for x in inputs};assert len(source)==200
records=rows(ROOT/'NATIVE_REQUEST_CAPTURE.jsonl.gz');assert len(records)==len(source)
seen=set();nrequests=0
for r in records:
 key=(r['task'],r['source_index']);assert key not in seen;seen.add(key)
 original=source[key]['record'];assert hashlib.sha256(canonical(original)).hexdigest()==r['source_sha256']
 opts=original['choices']['text'];q=original.get('question',original.get('question_stem'));gold=list(map(str,original['choices']['label'])).index(str(original['answerKey']))
 assert r['source_gold_index']==gold and r['identical_to_projection'] is True
 carrier=r['request_carrier'];assert len(carrier)==len(opts)
 assert [x['idx'] for x in carrier]==list(range(len(opts)))
 assert [x['continuation'] for x in carrier]==[' '+x for x in opts]
 assert all(q in x['context'] and x['request_type']=='loglikelihood' for x in carrier)
 nrequests+=len(carrier)
assert seen==set(source) and nrequests==801
fixture_count=0
for task in ['arc_challenge','openbookqa']:
 values=json.loads((ROOT/(task+'_FIXTURES.json')).read_text());assert len(values)==200
 for name,want in [('source_gold_positive',1),('nongold_positive',0)]:
  subset=[v for v in values if v['fixture']==name];assert len(subset)==100
  assert {v['source_index'] for v in subset}=={i for t,i in source if t==task}
  assert all(v['acc']==v['acc_norm']==want for v in subset)
 fixture_count+=len(values)
assert fixture_count==summary['constructed_fixture_evaluations']==400
provenance=json.loads((ROOT/'NATIVE_INSTALL_PROVENANCE.json').read_text());assert provenance['ast_projection'] is False and provenance['source_monkeypatches'] is False
assert provenance['commit']=='d6de81643928d653435c431bae19945d41d32520'
result=dict(status='PASS',installed_native_module_hashes_verified=len(provenance['native_source_sha256']),source_units=200,native_option_requests=801,constructed_fixture_evaluations=400,projection_carrier_differences=0,model_requests=0,scope='Native installed task/data/request/process_results path only; not model-backed or tokenizer execution.')
(ROOT/'VERIFICATION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))

