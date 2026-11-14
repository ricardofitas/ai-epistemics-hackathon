"""Native likelihood request construction using a documented dependency scaffold."""
import ast,copy,gzip,hashlib,json,logging,sys,types,shutil,re
from collections import Counter
from pathlib import Path
import yaml
from jinja2 import Environment,BaseLoader,StrictUndefined
ROOT=Path(__file__).resolve().parent
BASE=Path(sys.argv[1]).resolve();V2=Path(sys.argv[2]).resolve()
P=json.loads((ROOT/'PROTOCOL.json').read_text())
for name,key in [('check_contract.py','v1_sha256'),('source_bound.py','v2_sha256')]:
 assert hashlib.sha256((V2/name).read_bytes()).hexdigest()==P[key]
 shutil.copyfile(V2/name,ROOT/name)
sys.path.insert(0,str(ROOT))
from source_bound import audit_with_source,guarded_source_inference
from check_contract import InvalidContract
def canonical(x):return json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()
def lines(p):return [json.loads(x) for x in gzip.decompress(p.read_bytes()).splitlines()]
# The exact native Instance dataclass is executed as a real registered module.
module=types.ModuleType('native_harness_instance');sys.modules[module.__name__]=module
exec(compile((ROOT/'source/lm_eval_api_instance.py').read_text(),'native_instance','exec'),module.__dict__)
# Match the captured native environment exactly for these task templates.
env=Environment(loader=BaseLoader,undefined=StrictUndefined,keep_trailing_newline=True)
utils_tree=ast.parse((ROOT/'source/lm_eval_utils.py').read_text())
nodes=[n for n in utils_tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name in ['regex_replace','apply_template']]
utils_ns={'env':env,'re':re}
exec(compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),'native_template_functions','exec'),utils_ns)
env.filters['regex_replace']=utils_ns['regex_replace']
task_tree=ast.parse((ROOT/'source/lm_eval_api_task.py').read_text())
cls=next(n for n in task_tree.body if isinstance(n,ast.ClassDef) and n.name=='ConfigurableTask')
names=['doc_to_text','doc_to_choice','doc_to_target','construct_requests']
methods=[n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name in names]
assert len(methods)==4
projected=ast.ClassDef(name='NativeTaskProjection',bases=[],keywords=[],body=methods,decorator_list=[])
future=ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0)
ns={'ast':ast,'utils':types.SimpleNamespace(apply_template=utils_ns['apply_template']),'Instance':module.Instance,'deepcopy':copy.deepcopy,'eval_logger':logging.getLogger('harness_source_projection')}
exec(compile(ast.fix_missing_locations(ast.Module(body=[future,projected],type_ignores=[])),'native_task_projection','exec'),ns)
config_tree=ast.parse((ROOT/'source/lm_eval_config_task.py').read_text())
config_class=next(n for n in config_tree.body if isinstance(n,ast.ClassDef) and n.name=='TaskConfig')
defaults={n.target.id:ast.literal_eval(n.value) for n in config_class.body if isinstance(n,ast.AnnAssign) and isinstance(n.target,ast.Name) and n.target.id in ['target_delimiter','doc_to_image','doc_to_audio','gen_prefix','fewshot_delimiter']}
assert defaults['target_delimiter']==' '
def config_for(task):
 if task=='arc_challenge':
  config=yaml.safe_load((ROOT/'source/arc_easy.yaml').read_text());config.update(yaml.safe_load((ROOT/'source/arc_challenge.yaml').read_text()));config.pop('include',None)
 else:config=yaml.safe_load((ROOT/'source/openbookqa.yaml').read_text())
 return types.SimpleNamespace(**{**defaults,**config})
def task_for(task,doc):
 t=ns['NativeTaskProjection']();t.config=config_for(task);t._config=t.config;t.features=doc.keys();t.prompt=None;t.OUTPUT_TYPE=t.config.output_type;t.multiple_input=False;t._metric_fn_list={'acc':None,'acc_norm':None}
 return t
def wire_check(requests,context,question,options,delimiter):
 failures=[]
 if len(requests)!=len(options):failures.append('request_count_changed')
 if [r['continuation'] for r in requests]!=[delimiter+x for x in options]:failures.append('choice_continuations_changed')
 if any(r['context']!=context for r in requests):failures.append('context_changed')
 if not requests or any(question not in r['context'] for r in requests):failures.append('source_question_missing')
 return dict(status='FAIL' if failures else 'PASS',failures=failures)
records=[];selected_inputs=[];exceptions=[]
for task,name in [('arc_challenge','arc-challenge'),('openbookqa','openbookqa')]:
 allrows=lines(BASE/'work/holdout/capture'/name/'SOURCE_ROWS.jsonl.gz')
 ordering=sorted(range(len(allrows)),key=lambda i:(hashlib.sha256(b'harness-transfer-v1|'+canonical(allrows[i])).hexdigest(),i))[:100]
 for index in ordering:
  doc=allrows[index]
  try:
   selected_inputs.append(dict(task=task,source_index=index,source_sha256=hashlib.sha256(canonical(doc)).hexdigest(),record=doc))
   opts=list(doc['choices']['text']);gold_index=list(map(str,doc['choices']['label'])).index(str(doc['answerKey']));q=doc['question'] if task=='arc_challenge' else doc['question_stem']
   t=task_for(task,doc);context=t.doc_to_text(doc);native_choices=t.doc_to_choice(doc);target=t.doc_to_target(doc)
   assert native_choices==opts and target==gold_index
   nonce=copy.deepcopy(doc);nonce['question' if task=='arc_challenge' else 'question_stem']='QUESTION_MUTATION_NONCE'
   changed=t.doc_to_text(nonce)!=context
   wrong=next(i for i in range(len(opts)) if i!=gold_index)
   for condition in P['conditions']:
    declared_context=context+'\n\n' if condition=='benign_context_spacing' else context
    native=t.construct_requests(doc,declared_context)
    carrier=[dict(context=r.arguments[0],continuation=r.arguments[1],idx=r.idx,request_type=r.request_type) for r in native]
    assert all(r['request_type']=='loglikelihood' for r in carrier)
    rec=dict(schema_version=1,row_id=task+':'+str(index)+':'+condition,kind='choice',prompt=declared_context,choices=native_choices,correct_text=opts[gold_index],expected_reference=chr(65+gold_index),reference=chr(65+target),question_probe_changed=changed,context_required=False,source_question=q,source_choices=opts,source_correct_index=gold_index)
    if condition=='drop_continuation':carrier.pop(wrong)
    if condition=='replace_continuation':carrier[wrong]['continuation']=' NON_SOURCE_CONTINUATION'
    if condition=='omit_question_context':
     for r in carrier:r['context']='NON_SOURCE_CONTEXT'
    v2=audit_with_source([rec]);wire=wire_check(carrier,declared_context,q,opts,t.config.target_delimiter)
    observed_calls=[]
    def counting_backend(request_bundle):
     observed_calls.append(len(request_bundle))
     return len(request_bundle)
    def guarded_send():
     if wire['status']!='PASS':raise InvalidContract(wire)
     return guarded_source_inference([rec],lambda prompts:counting_backend(carrier))
    try:guarded_send()
    except InvalidContract:pass
    backend_calls=len(observed_calls)
    records.append(dict(task=task,source_index=index,condition=condition,source_target=gold_index,native_target=target,adapter_record=rec,actual_requests=carrier,v2=v2,wire=wire,constructed_backend_calls=backend_calls))
  except Exception as e:exceptions.append(dict(task=task,source_index=index,error_type=type(e).__name__,error=str(e)))
summary=[]
for task in ['arc_challenge','openbookqa']:
 for condition in P['conditions']:
  subset=[r for r in records if r['task']==task and r['condition']==condition]
  summary.append(dict(task=task,condition=condition,rows=len(subset),v2_statuses=dict(Counter(r['v2']['status'] for r in subset)),wire_statuses=dict(Counter(r['wire']['status'] for r in subset)),constructed_backend_calls=sum(r['constructed_backend_calls'] for r in subset)))
for name,rows in [('SELECTED_INPUTS.jsonl.gz',selected_inputs),('REQUEST_CAPTURE.jsonl.gz',records)]:
 (ROOT/name).write_bytes(gzip.compress(b''.join(canonical(r)+b'\n' for r in rows),mtime=0))
result=dict(engine_revision=P['engine_revision'],source_units=len(selected_inputs),condition_records=len(records),exceptions=exceptions,provider_model_calls=0,scope=P['source_scope'],source_data_reused=True,summary=summary)
(ROOT/'RESULTS.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))

