import json,gzip,copy,hashlib,urllib.request,traceback,platform
from pathlib import Path
from types import SimpleNamespace
from collections import Counter
import pandas as pd
import native_scaffold as native
P=Path(__file__).resolve().parent
canonical=lambda v:json.dumps(v,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()
def dump(n,v):(P/n).write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
def gz(n,v):(P/n).write_bytes(gzip.compress(b''.join(canonical(x)+b'\n' for x in v),mtime=0))
proto=json.loads((P/'PROTOCOL.json').read_text());gallery=json.loads((P/'GALLERY_ENTRY.json').read_text());captures=[];selection=[];errors=[];acquisition=[];summary={}
assert hashlib.sha256((P/'GALLERY_ENTRY.json').read_bytes()).hexdigest()==proto['gallery_entry_sha256']
for n,h in proto['upstream_hashes'].items():assert hashlib.sha256((P/'upstream'/n).read_bytes()).hexdigest()==h
for split,path in proto['paths'].items():
 try:
  u='https://huggingface.co/datasets/'+proto['source_repository']+'/resolve/'+proto['source_revision']+'/'+path
  with urllib.request.urlopen(u,timeout=45) as response:raw=response.read(15_000_001);status=response.status
  assert len(raw)<=15_000_000;(P/(split+'.jsonl')).write_bytes(raw);acquisition.append(dict(url=u,status=status,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()));dump('ACQUISITION.json',acquisition)
  rows=[json.loads(x) for x in raw.splitlines()];order=sorted(range(len(rows)),key=lambda i:(hashlib.sha256(canonical(rows[i])).hexdigest(),i))[:100]
  chosen=[dict(split=split,source_index=i,record=rows[i],source_sha256=hashlib.sha256(canonical(rows[i])).hexdigest()) for i in order];selection+=chosen
  for condition in proto['conditions']:
   precls,gencls=native.load_native_classes();pre=precls.__new__(precls);entry=copy.deepcopy(gallery);mapping=copy.deepcopy(entry['meta']['key_mapping']);evaltype=entry['bench_dataflow_eval_type']
   if condition in ['bind_only','bind_and_type']:native.bind_source_symbols(entry,mapping)
   if condition=='bind_and_type' and split=='free_form':
    evaltype='key2_q_ma';entry['meta']['prompt']['user_template']=entry['meta']['prompt']['user_template'].replace('{choices_text}','').replace('Select the best option and give the final answer as <answer>CHOICE</answer>.','Answer the question in free text.')
   frame,mapping=pre._preprocess_dataframe(pd.DataFrame([s['record'] for s in chosen]),'mixeval',mapping,eval_type=evaltype)
   template,_=pre._resolve_prompt_template(SimpleNamespace(meta=entry['meta'],bench_prompt_template=None),evaltype);sink=native.RecordedServing();op=gencls(eval_type=evaltype,llm_serving=sink,prompt_template=template,force_generate=True);storage=native.FrameStorage(frame);op.run(storage=storage,input_question_key=mapping['input_question_key'],input_choices_key=mapping.get('input_choices_key'),input_context_key=mapping.get('input_context_key'),output_key='generated_ans');assert len(sink.prompts)==len(chosen)
   panel=[]
   for s,row,prompt in zip(chosen,frame.to_dict('records'),sink.prompts):
    official=s['record'];q=str(row[mapping['input_question_key']]);ctx=op._normalize_context(row.get(mapping.get('input_context_key')));choices=op._ensure_list(row.get(mapping.get('input_choices_key')));nonce=op._build_prompt(eval_type=evaltype,question='QUESTION_NONCE_MIXEVAL',context=ctx,choices=choices)
    kind=official.get('problem_type');expected_kind='free-form' if split=='free_form' else 'single-choice';type_ok=(kind==expected_kind and (evaltype=='key2_q_ma' if split=='free_form' else evaltype=='key3_q_choices_a'))
    keys=list(gallery['meta']['key_mapping'].values());schema=all(k in official for k in keys if isinstance(k,str));options=official.get('options');targets=official.get('target');valid_target=(isinstance(targets,list) and bool(targets))
    if split=='multiple_choice':valid_target=valid_target and all(str(t).isdigit() and 0<=int(t)<len(options or []) for t in targets)
    item=dict(split=split,source_index=s['source_index'],condition=condition,source_sha256=s['source_sha256'],problem_type=kind,configured_eval_type=evaltype,field_presence_check=schema,metadata_route_parser_consistent=evaltype=='key3_q_choices_a',source_type_preserved=type_ok,question_bound=prompt!=nonce,choices_preserved=choices==options if split=='multiple_choice' else None,source_targets_valid=valid_target,displayed_choices=choices,MC_instruction='Select the best option' in prompt,prompt=prompt,prompt_sha256=hashlib.sha256(prompt.encode()).hexdigest());panel.append(item);captures.append(item)
   summary[split+':'+condition]=dict(rows=len(panel),recording_sink_calls=sink.calls,**{k:sum(bool(x[k]) for x in panel) for k in ['field_presence_check','metadata_route_parser_consistent','source_type_preserved','question_bound','choices_preserved','source_targets_valid','MC_instruction']})
 except Exception as e:errors.append(dict(split=split,error=repr(e),traceback=traceback.format_exc()))
gz('SELECTED.jsonl.gz',selection);gz('CAPTURES.jsonl.gz',captures);dump('ERRORS.json',errors);dump('ACQUISITION.json',acquisition);dump('SUMMARY.json',dict(status='completed' if not errors else 'partial',source_rows_selected=len(selection),condition_records=len(captures),panels=summary,errors=errors,provider_model_calls=0,scope=proto['scope']));dump('RUNTIME.json',dict(python=platform.python_version(),pandas=pd.__version__));print((P/'SUMMARY.json').read_text())
