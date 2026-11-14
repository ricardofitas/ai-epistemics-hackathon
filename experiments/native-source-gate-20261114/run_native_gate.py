"""Installed native task route into source-anchored immutable gate; no models."""
import os,json,gzip,hashlib,copy,traceback,importlib.metadata
from pathlib import Path
from collections import defaultdict,Counter
from native_source_gate import SourceGate,Blocked,sha
P=Path(__file__).resolve().parent
for k in ['HF_DATASETS_OFFLINE','HF_HUB_OFFLINE','HF_HUB_DISABLE_TELEMETRY']:os.environ[k]='1'
def dump(n,v):(P/n).write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
def readrows(p):return [json.loads(x) for x in gzip.decompress(p.read_bytes()).splitlines()]
proto=json.loads((P/'PROTOCOL.json').read_text());records=[];errors=[];natural=0
try:
 import lm_eval
 from lm_eval.api.task import ConfigurableTask
 source_provenance=json.loads((P/'input/NATIVE_INSTALL_PROVENANCE.json').read_text());root=Path(lm_eval.__file__).parent;actual={}
 for rel,want in source_provenance['native_source_sha256'].items():
  actual[rel]=hashlib.sha256((root/rel).read_bytes()).hexdigest();assert actual[rel]==want
 dependencies={n:importlib.metadata.version(n) for n in source_provenance['dependencies']};assert dependencies==source_provenance['dependencies']
 assert hashlib.sha256((P/'native_source_gate.py').read_bytes()).hexdigest()==proto['gate_sha256']
 for n,want in proto['input_files_sha256'].items():assert hashlib.sha256((P/n).read_bytes()).hexdigest()==want
 dump('RUNTIME_PROVENANCE.json',dict(engine_revision=proto['engine_revision'],native_module_sha256=actual,dependencies=dependencies,package_root=str(root),ast_projection=False,source_monkeypatch=False,models_instantiated=0))
 inputs=readrows(P/'input/SELECTED_INPUTS.jsonl.gz');registry={}
 for task_name in ['arc_challenge','openbookqa']:
  subset=[s for s in inputs if s['task']==task_name];assert len(subset)==100
  for i,s in enumerate(subset):
   assert sha(s['record'])==s['source_sha256'];registry[task_name+':'+str(s['source_index'])]={**s,'native_doc_id':i}
 gate=SourceGate(registry)
 for task_name in ['arc_challenge','openbookqa']:
  subset=[s for s in inputs if s['task']==task_name];data=P/(task_name+'.jsonl');data.write_text(''.join(json.dumps(s['record'],ensure_ascii=False)+'\n' for s in subset));cfg=json.loads((P/'input'/str(task_name+'_CONFIG.json')).read_text());cfg.update(task='native_gate_'+task_name,dataset_kwargs={'data_files':{'test':str(data)}})
  dump(task_name+'_RESOLVED_CONFIG.json',cfg);task=ConfigurableTask(config=cfg,cache_dir=str(P/'dataset_cache'));task.set_fewshot_seed(20261114);task.build_all_requests(limit=100,rank=0,world_size=1,cache_requests=False,apply_chat_template=False)
  bydoc=defaultdict(list)
  for r in task.instances:bydoc[r.doc_id].append(r)
  for i,s in enumerate(subset):
   key=task_name+':'+str(s['source_index']);original=s['record'];items=sorted(bydoc[i],key=lambda r:r.idx);assert items;natural+=len(items);ref=task.doc_to_target(original);question=original['question'] if task_name=='arc_challenge' else original['question_stem'];position=list(map(str,original['choices']['label'])).index(str(original['answerKey']));wrong=next(k for k in range(len(items)) if k!=position)
   for condition in proto['conditions']:
    mutated=copy.deepcopy(items);target=ref;lookup=key
    if condition=='benign_context_spacing':
     for r in mutated:r.arguments=(r.args[0]+' \n',r.args[1])
    elif condition=='drop_continuation':mutated.pop(wrong)
    elif condition=='replace_continuation':mutated[wrong].arguments=(mutated[wrong].args[0],' REPLACED_CONTINUATION_'+key)
    elif condition=='omit_question':
     for r in mutated:r.arguments=(r.args[0].replace(question,''),r.args[1])
    elif condition=='wrong_reference':target=wrong
    elif condition=='substitute_document':
     for r in mutated:r.doc['question' if task_name=='arc_challenge' else 'question_stem']='SUBSTITUTED_SOURCE_'+key
    elif condition=='missing_trusted_source':lookup='UNKNOWN:'+key
    sink_calls=[]
    def sink(snapshot):
     sink_calls.append(dict(snapshot_sha256=sha(snapshot),option_requests=len(snapshot)));return len(snapshot)
    try:report,result=gate.dispatch(lookup,mutated,target,sink)
    except Blocked as e:report=e.report
    records.append(dict(source_key=key,source_sha256=s['source_sha256'],condition=condition,report=report,sink_calls=sink_calls,reference=target,native_documents_sha256=[sha(r.doc) for r in mutated],carrier=[dict(request_type=r.request_type,doc_id=r.doc_id,idx=r.idx,context=r.args[0],continuation=r.args[1]) for r in mutated]))
except Exception as e:errors.append(dict(type=type(e).__name__,message=str(e),traceback=traceback.format_exc()))
(P/'RESULTS.jsonl.gz').write_bytes(gzip.compress(b''.join(json.dumps(r,ensure_ascii=False).encode()+b'\n' for r in records),mtime=0));dump('ERRORS.json',errors)
summary=dict(status='completed' if not errors else 'integration_error',source_units=len({r['source_key'] for r in records}),native_option_requests=natural,condition_records=len(records),statuses=dict(Counter(r['report']['status'] for r in records)),conditions={c:dict(Counter(r['report']['status'] for r in records if r['condition']==c)) for c in proto['conditions']},counting_sink_invocations=sum(len(r['sink_calls']) for r in records),dispatched_option_requests=sum(k['option_requests'] for r in records for k in r['sink_calls']),provider_model_calls=0,errors=errors,scope=proto['stage'],limits=proto['limits'])
dump('SUMMARY.json',summary);print(json.dumps(summary,indent=2))
raise SystemExit(0 if not errors else 1)
