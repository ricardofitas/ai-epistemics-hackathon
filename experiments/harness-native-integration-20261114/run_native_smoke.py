"""Execute installed native task APIs offline; constructed likelihood fixtures only."""
import os,sys,json,gzip,copy,hashlib,inspect,importlib.metadata,traceback,subprocess
from pathlib import Path
from collections import defaultdict
ROOT=Path(__file__).resolve().parent;PRIOR=Path(sys.argv[1]).resolve();CHECKOUT=Path(sys.argv[2]).resolve()
def dump(n,v):(ROOT/n).write_text(json.dumps(v,indent=2,ensure_ascii=False,default=str)+'\n')
def rows(p):return [json.loads(x) for x in gzip.decompress(p.read_bytes()).splitlines()]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
os.environ['HF_DATASETS_OFFLINE']='1';os.environ['HF_HUB_OFFLINE']='1';os.environ['HF_HUB_DISABLE_TELEMETRY']='1'
results=[];captures=[];errors=[]
try:
 import yaml,lm_eval,lm_eval.api.task,lm_eval.config.task,lm_eval.api.instance,lm_eval.api.metrics,lm_eval.utils
 from lm_eval.api.task import ConfigurableTask
 import datasets
 expected=json.loads((ROOT/'PROTOCOL.json').read_text())
 commit=subprocess.check_output(['git','-C',str(CHECKOUT),'rev-parse','HEAD'],text=True).strip()
 assert commit==expected['engine_revision']
 root=Path(lm_eval.__file__).parent
 package_files=['__init__.py','api/task.py','config/task.py','api/instance.py','api/metrics.py','utils.py']
 source_checks={}
 for rel in package_files:
  a=root/rel;b=CHECKOUT/'lm_eval'/rel;assert a.read_bytes()==b.read_bytes();source_checks[rel]=sha(a)
 dump('NATIVE_INSTALL_PROVENANCE.json',dict(commit=commit,lm_eval_version=lm_eval.__version__,installed_package_root=str(root),native_source_sha256=source_checks,dependencies={n:importlib.metadata.version(n) for n in ['lm_eval','datasets','evaluate','Jinja2','PyYAML','numpy','torch']},ast_projection=False,source_monkeypatches=False))
 source=rows(PRIOR/'SELECTED_INPUTS.jsonl.gz');assert len(source)==200
 old=[r for r in rows(PRIOR/'REQUEST_CAPTURE.jsonl.gz') if r['condition']=='native']
 previous={(r['task'],r['source_index']):r for r in old}
 for task_name in ['arc_challenge','openbookqa']:
  selected=[r for r in source if r['task']==task_name];assert len(selected)==100
  data_path=ROOT/(task_name+'.jsonl');data_path.write_text(''.join(json.dumps(r['record'],ensure_ascii=False)+'\n' for r in selected))
  if task_name=='arc_challenge':
   cfg=yaml.safe_load((CHECKOUT/'lm_eval/tasks/arc/arc_easy.yaml').read_text());cfg.update(yaml.safe_load((CHECKOUT/'lm_eval/tasks/arc/arc_challenge.yaml').read_text()));cfg.pop('include',None)
  else:cfg=yaml.safe_load((CHECKOUT/'lm_eval/tasks/openbookqa/openbookqa.yaml').read_text())
  cfg.update(task='contract_native_smoke_'+task_name,dataset_path='json',dataset_name=None,dataset_kwargs={'data_files':{'test':str(data_path)}},training_split=None,validation_split=None,test_split='test',num_fewshot=0)
  dump(task_name+'_CONFIG.json',cfg)
  native=ConfigurableTask(config=cfg,cache_dir=str(ROOT/'dataset_cache'))
  native.set_fewshot_seed(20261114)
  docs=list(native.test_docs());assert len(docs)==len(selected)
  native.build_all_requests(limit=len(docs),rank=0,world_size=1,cache_requests=False,apply_chat_template=False)
  instances=list(native.instances);bydoc=defaultdict(list)
  for instance in instances:bydoc[instance.doc_id].append(instance)
  assert set(bydoc)==set(range(100))
  mismatches=[];fixtures=[];task_requests=0
  for index,(doc,s) in enumerate(zip(docs,selected)):
   original=s['record'];opts=list(original['choices']['text']);position=list(map(str,original['choices']['label'])).index(str(original['answerKey']));q=original['question'] if task_name=='arc_challenge' else original['question_stem']
   assert doc==original
   assert native.doc_to_choice(doc)==opts and native.doc_to_target(doc)==position
   records=sorted(bydoc[index],key=lambda x:x.idx);assert len(records)==len(opts)
   carrier=[dict(context=r.args[0],continuation=r.args[1],idx=r.idx,request_type=r.request_type) for r in records]
   assert all(r['request_type']=='loglikelihood' and q in r['context'] for r in carrier)
   assert [r['continuation'] for r in carrier]==[native.config.target_delimiter+text for text in opts]
   prior=previous[(task_name,s['source_index'])]['actual_requests']
   identical=carrier==prior
   if not identical:mismatches.append(dict(source_index=s['source_index'],prior=prior,installed_driver=carrier))
   wrong=next(j for j in range(len(opts)) if j!=position)
   for name,target,want in [('source_gold_positive',position,1),('nongold_positive',wrong,0)]:
    logprobs=[(2.0 if j==target else -2.0,True) for j in range(len(opts))]
    metrics=native.process_results(doc,logprobs)
    assert float(metrics['acc'])==want and float(metrics['acc_norm'])==want
    fixtures.append(dict(source_index=s['source_index'],fixture=name,acc=float(metrics['acc']),acc_norm=float(metrics['acc_norm'])))
   task_requests+=len(carrier)
   captures.append(dict(task=task_name,source_index=s['source_index'],native_doc_id=index,source_sha256=s['source_sha256'],source_gold_index=position,request_carrier=carrier,identical_to_projection=identical))
  results.append(dict(task=task_name,status='completed',source_rows=len(docs),native_request_objects=task_requests,fixture_evaluations=len(fixtures),source_gold_fixture_correct=sum(x['acc']==1 for x in fixtures if x['fixture']=='source_gold_positive'),nongold_fixture_rejected=sum(x['acc']==0 for x in fixtures if x['fixture']=='nongold_positive'),projection_carrier_differences=len(mismatches)))
  dump(task_name+'_CARRIER_DIFFERENCES.json',mismatches);dump(task_name+'_FIXTURES.json',fixtures);dump('TASK_RESULTS.json',results)
except Exception as error:
 errors.append(dict(type=type(error).__name__,message=str(error),traceback=traceback.format_exc()))
dump('ERRORS.json',errors)
(ROOT/'NATIVE_REQUEST_CAPTURE.jsonl.gz').write_bytes(gzip.compress(b''.join(json.dumps(r,ensure_ascii=False).encode()+b'\n' for r in captures),mtime=0))
summary=dict(status='completed' if not errors else 'integration_error',source_units_completed=sum(r['source_rows'] for r in results),native_option_requests=sum(r['native_request_objects'] for r in results),constructed_fixture_evaluations=sum(r['fixture_evaluations'] for r in results),projection_carrier_differences=sum(r['projection_carrier_differences'] for r in results),provider_model_calls=0,model_backends_instantiated=0,errors=errors,tasks=results,scope=expected['scope'] if 'expected' in globals() else 'Native package import failed before cases')
dump('SUMMARY.json',summary);print(json.dumps(summary,indent=2))
sys.exit(0 if not errors else 1)
