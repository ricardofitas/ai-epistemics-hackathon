"""Pinned public-response replay with ordinary original parser/scorer imports."""
from pathlib import Path
import sys,os,json,gzip,hashlib,urllib.request,random,traceback
from collections import defaultdict,Counter
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P/'packages'))
os.environ['HF_HUB_OFFLINE']='1';os.environ['HF_HUB_DISABLE_TELEMETRY']='1'
import typed_contract as typed
from one_eval.metrics.parsers import parse_value
proto=json.loads((P/'PROTOCOL.json').read_text());gallery=json.loads((P/'input/GALLERY_ENTRY.json').read_text());native_cfg=gallery['meta']['evaluation']['parser']
canonical=lambda v:json.dumps(v,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()
sha=lambda b:hashlib.sha256(b).hexdigest()
rows=lambda path:[json.loads(x) for x in gzip.decompress(path.read_bytes()).splitlines()]
def dump(n,v):(P/n).write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
def gz(n,v):(P/n).write_bytes(gzip.compress(b''.join(canonical(x)+b'\n' for x in v),mtime=0))
def identity(r,split):return canonical([split,r.get('context') or '',r['prompt'],list(map(str,r['target'])),r['options'] if split=='multiple_choice' else None])
def native_score(r,out):
 ref=parse_value(r['target'],native_cfg,r);pred=parse_value(out,native_cfg,r)
 return dict(reference_ok=ref.ok,reference_normalized=ref.normalized,reference_error=ref.error,prediction_ok=pred.ok,prediction_normalized=pred.normalized,prediction_error=pred.error,score=int(ref.normalized==pred.normalized) if ref.ok and pred.ok else 0 if ref.ok else None)
selected=rows(P/'input/SELECTED.jsonl.gz');assert len(selected)==200
capture=[];fixtures=[];prompts=[];errors=[];acq=[];coverage=[];summaries={}
for x in json.loads((P/'SOURCE_MODULE_PROVENANCE.json').read_text()):assert sha((P/'packages'/x['path']).read_bytes())==x['sha256']
random.seed(42)
for split,info in proto['public_outputs']['files'].items():
 try:
  u='https://raw.githubusercontent.com/JinjieNi/MixEval/'+proto['official_revision']+'/'+info['path'];path=P/(split+'_public_responses.jsonl')
  with urllib.request.urlopen(u,timeout=50) as response:raw=response.read(10_000_001)
  assert len(raw)<=10_000_000 and hashlib.sha1(('blob '+str(len(raw))+'\0').encode()+raw).hexdigest()==info['git_blob'];path.write_bytes(raw);acq.append(dict(url=u,bytes=len(raw),sha256=sha(raw),git_blob=info['git_blob']));dump('ACQUISITION.json',acq)
  published=[json.loads(line) for line in raw.splitlines() if line.strip()];lookup=defaultdict(list)
  for i,r in enumerate(published):lookup[identity(r,split)].append((i,r))
  for s in [s for s in selected if s['split']==split]:
   r=s['record'];key=dict(split=split,source_index=s['source_index'],source_sha256=s['source_sha256']);matches=lookup.get(identity(r,split),[])
   prompt=typed.generate_prompt(r,split);assert r['prompt'] in prompt
   prompts.append(dict(**key,config=typed.describe(r,split),prompt=prompt,prompt_sha256=sha(prompt.encode())))
   oracle=r['target'][0] if split=='free_form' else chr(65+int(r['target'][0]));fix=typed.evaluate(r,oracle,split);fixtures.append(dict(**key,fixture='official_gold_text_or_letter',output=oracle,typed=fix))
   if len(matches)!=1:coverage.append(dict(**key,disposition='unmatched' if not matches else 'ambiguous',matches=len(matches)));continue
   i,cached=matches[0];out=cached.get('response')
   if not isinstance(out,str):coverage.append(dict(**key,disposition='response_missing_or_nontext',public_row=i));continue
   try:
    n=native_score(r,out);t=typed.evaluate(r,out,split)
    capture.append(dict(**key,public_row=i,public_id=cached.get('id'),disposition='completed',captured_text=out,captured_text_sha256=sha(out.encode()),native=n,typed=t,synthetic=False))
    coverage.append(dict(**key,disposition='completed',public_row=i))
   except Exception as e:errors.append(dict(**key,error=repr(e)));coverage.append(dict(**key,disposition='parse_or_score_error',public_row=i,error=repr(e)))
 except Exception as e:errors.append(dict(split=split,stage='acquisition_or_setup',error=repr(e),traceback=traceback.format_exc()))
 subset=[x for x in capture if x['split']==split];typed_correct=sum(x['typed']['score'] for x in subset);native_valid=[x for x in subset if x['native']['score'] is not None];native_correct=sum(x['native']['score'] for x in native_valid);missing=100-len(subset);nunknown=100-len(native_valid)
 summaries[split]=dict(fixed_source_rows=100,public_rows_in_file=len(published) if 'published' in locals() else None,uniquely_matched_texts=len(subset),native_reference_valid=len(native_valid),native_reference_invalid=len(subset)-len(native_valid),native_correct=native_correct,native_valid_only_accuracy=native_correct/len(native_valid) if native_valid else None,typed_correct=typed_correct,typed_accuracy_among_matched=typed_correct/len(subset) if subset else None,typed_all_source_bounds=[typed_correct/100,(typed_correct+missing)/100],native_all_source_bounds=[native_correct/100,(native_correct+nunknown)/100],paired_gain_bounds=[(typed_correct-native_correct-nunknown)/100,(typed_correct+missing-native_correct)/100],paired_scoring_disagreements=sum(x['native']['score'] is not None and x['native']['score']!=x['typed']['score'] for x in subset),typed_random_fallbacks=sum(x['typed']['random_fallback'] for x in subset),native_prediction_parse_failures=sum(not x['native']['prediction_ok'] for x in subset))
gz('CAPTURES.jsonl.gz',capture);gz('CONTRACT_CAPTURE.jsonl.gz',prompts);gz('ORACLE_FIXTURES.jsonl.gz',fixtures);dump('COVERAGE.json',coverage);dump('ERRORS.json',errors);dump('SUMMARY.json',dict(status='completed' if not errors else 'partial',panels=summaries,captured_real_outputs=len(capture),synthetic_oracle_fixtures=len(fixtures),fixture_correct=sum(x['typed']['score'] for x in fixtures),contract_prompts=len(prompts),ordinary_unmodified_official_module_imports=True,ast_projection=False,new_provider_calls=0,models_instantiated=0,errors=errors,scope='Fixed-public-output replay under native choice contract vs explicitly typed official rule mode, not default model-judge score or original faulty-prompt inference.'))
print((P/'SUMMARY.json').read_text())
