"""Independent source identity/cached text/score/unknown reconciliation."""
from pathlib import Path
from collections import defaultdict,Counter
import json,gzip,hashlib,sys,random
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P/'packages'))
from mix_eval.utils.metric_utils import parse_freeform_response_rule,eval_freeform_rule,parse_multi_choice_response_rule,eval_multi_choice
from one_eval.metrics.parsers import parse_value
from types import SimpleNamespace
canon=lambda v:json.dumps(v,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()
sha=lambda b:hashlib.sha256(b).hexdigest()
rows=lambda n:[json.loads(x) for x in gzip.decompress((P/n).read_bytes()).splitlines()]
selected=rows('input/SELECTED.jsonl.gz');source={(s['split'],s['source_index']):s for s in selected};assert len(source)==200
identity=lambda r,split:canon([split,r.get('context') or '',r['prompt'],list(map(str,r['target'])),r['options'] if split=='multiple_choice' else None])
proto=json.loads((P/'PROTOCOL.json').read_text());summary=json.loads((P/'SUMMARY.json').read_text());cfg=json.loads((P/'input/GALLERY_ENTRY.json').read_text())['meta']['evaluation']['parser'];lookup={}
for split in proto['public_outputs']['files']:
 raw=(P/(split+'_public_responses.jsonl')).read_bytes();want=proto['public_outputs']['files'][split]['git_blob'];assert hashlib.sha1(('blob '+str(len(raw))+'\0').encode()+raw).hexdigest()==want
 lookup[split]=defaultdict(list)
 for i,r in enumerate(json.loads(x) for x in raw.splitlines() if x.strip()):lookup[split][identity(r,split)].append((i,r))
coverage=json.loads((P/'COVERAGE.json').read_text());assert len(coverage)==200 and len({(r['split'],r['source_index']) for r in coverage})==200
for r in coverage:
 s=source[(r['split'],r['source_index'])];m=lookup[r['split']][identity(s['record'],r['split'])]
 assert (len(m)==1 if r['disposition']=='completed' else len(m)==0 if r['disposition']=='unmatched' else len(m)>1)
real=rows('CAPTURES.jsonl.gz');assert len(real)==49 and all(r['synthetic'] is False for r in real);random.seed(42);args=SimpleNamespace(model_type='ChatModel');fallbacks=[]
for c in real:
 r=source[(c['split'],c['source_index'])]['record'];m=lookup[c['split']][identity(r,c['split'])];assert len(m)==1 and m[0][0]==c['public_row'];out=m[0][1]['response'];assert out==c['captured_text'] and sha(out.encode())==c['captured_text_sha256']
 ref=parse_value(r['target'],cfg,r);pred=parse_value(out,cfg,r);assert ref.ok==c['native']['reference_ok'] and pred.ok==c['native']['prediction_ok'];assert c['native']['score'] is None and not ref.ok
 if c['split']=='free_form':parsed=parse_freeform_response_rule(args,out);score=int(eval_freeform_rule(r['target'],parsed));assert set(map(str,parsed))==set(map(str,c['typed']['parsed']))
 else:
  letters=[chr(65+i) for i in range(len(r['options']))];before=random.getstate();parsed=parse_multi_choice_response_rule(args,out,letters,dict(zip(letters,r['options'])));fallback=random.getstate()!=before;assert fallback==c['typed']['random_fallback'];score=int(eval_multi_choice([letters[int(t)] for t in r['target']],parsed));assert parsed==c['typed']['parsed']
  if fallback:fallbacks.append(c)
 assert score==c['typed']['score']
fixtures=rows('ORACLE_FIXTURES.jsonl.gz');assert len(fixtures)==200;failed=[c for c in fixtures if not c['typed']['score']];assert len(failed)==2 and all(c['split']=='free_form' for c in failed)
for f in fixtures:
 r=source[(f['split'],f['source_index'])]['record']
 if f['split']=='free_form':assert f['output']==r['target'][0] and int(eval_freeform_rule(r['target'],parse_freeform_response_rule(args,f['output'])))==f['typed']['score']
prompts=rows('CONTRACT_CAPTURE.jsonl.gz');assert len(prompts)==200
for c in prompts:
 r=source[(c['split'],c['source_index'])]['record'];assert r['prompt'] in c['prompt'] and sha(c['prompt'].encode())==c['prompt_sha256'];assert c['config']['parser'].endswith('freeform' if c['split']=='free_form' else 'choice');assert 'choice_letter' not in str(c['config'])
for split,count,right in [('free_form',17,13),('multiple_choice',32,20)]:
 rs=[c for c in real if c['split']==split];s=summary['panels'][split];assert len(rs)==count and sum(c['typed']['score'] for c in rs)==right and s['native_reference_valid']==0 and s['typed_correct']==right
for f in json.loads((P/'SOURCE_MODULE_PROVENANCE.json').read_text()):assert sha((P/'packages'/f['path']).read_bytes())==f['sha256']
report=dict(status='PASS',source_rows=200,uniquely_matched_cached_outputs=49,reference_exclusions_native=49,typed_correct={'free_form':13,'multiple_choice':20},typed_denominators={'free_form':17,'multiple_choice':32},oracle_controls={'total':200,'pass':198,'counterexamples':2},choice_random_fallback={'cases':len(fallbacks),'correct_with_seed42':sum(c['typed']['score'] for c in fallbacks),'correct_without_fallback':20-sum(c['typed']['score'] for c in fallbacks),'matched_denominator':32},initial_cohort_not_expanded=True,new_provider_calls=0,source_and_module_hashes_verified=True,scope='Separate source/identity/capture and ordinary original-scoring re-evaluation by same executor; no human gold audit or default model-judge run.')
(P/'VERIFICATION.json').write_text(json.dumps(report,indent=2)+'\n');(P/'RULE_COUNTEREXAMPLES.json').write_text(json.dumps(failed,indent=2)+'\n');print(json.dumps(report))
