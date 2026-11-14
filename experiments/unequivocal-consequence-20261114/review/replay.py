"""Reference-only WinoGrande consequence proof on authenticated archived outputs.

No generation is performed. Original registered choice metric/parser/runner and
BenchInfo execute through ordinary imports. Only the preprocessor class uses its
unchanged AST body to avoid unrelated provider imports. Offline metric replay.
"""
from pathlib import Path
from collections import Counter
import argparse,ast,copy,gzip,hashlib,importlib.util,json,re,sys,tempfile,zipfile
import logging
from typing import Any,Dict,List,Optional
import pandas as pd

MODEL_SHA='2a9abd3fd0c5f9108dd4c3812fba5d64c168b6e414d34e3b41191df869ba13df'
SOURCE_SHA='a43b28ce6c9219c7c2155d979b2df2a54645e636f1ef1384256522c238a90a39'
REV='8aba20ad17ee2c7d2391162ac03ffaebcbb17506'
HERE=Path(__file__).resolve().parent
def digest(raw):return hashlib.sha256(raw).hexdigest()
def compact(x):return json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':'),default=str)
def sha_obj(x):return digest(compact(x).encode())
def load_py(path,name):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def preprocessor(path):
 tree=ast.parse(path.read_text());node=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='DataFlowEvalTool')
 ns=dict(pd=pd,json=json,re=re,Path=Path,Any=Any,Dict=Dict,List=List,Optional=Optional,log=logging.getLogger('source_preprocessing'))
 future=ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0)
 exec(compile(ast.fix_missing_locations(ast.Module(body=[future,node],type_ignores=[])),str(path),'exec'),ns)
 return ns['DataFlowEvalTool'].__new__(ns['DataFlowEvalTool'])
def parse_final(text):
 found=re.findall(r'<answer>\s*([AB])\s*</answer>',text or '')
 return found[0] if len(found)==1 else None

def main():
 p=argparse.ArgumentParser();p.add_argument('--support-dir',type=Path,required=True)
 p.add_argument('--preprocessor',type=Path,required=True)
 p.add_argument('--model-archive',type=Path,default=HERE/'model-capture.zip');p.add_argument('--source-archive',type=Path,default=HERE/'source-capture.zip')
 p.add_argument('--out-dir',type=Path,default=HERE/'proof');a=p.parse_args();a.out_dir.mkdir(parents=True,exist_ok=True)
 assert digest(a.model_archive.read_bytes())==MODEL_SHA
 assert digest(a.source_archive.read_bytes())==SOURCE_SHA
 with zipfile.ZipFile(a.model_archive) as z:
  cases_bytes=z.read('cases.json');manifest_bytes=z.read('manifest.jsonl');responses_bytes=z.read('responses.jsonl')
 cases=json.loads(cases_bytes);manifest=[json.loads(x) for x in manifest_bytes.splitlines()];responses=[json.loads(x) for x in responses_bytes.splitlines()]
 assert len(cases)==48 and len(manifest)==len(responses)==96
 assert digest(cases_bytes)=='1c46423b72e1de9d6c0958bba5cb3973f9991e8fd4d701b4ea076beba338544f'
 assert digest(manifest_bytes)=='dc0d4995c2f4d9e79f14e4b4069aa94caa3126385d3808bbac3d083a40d6f075'
 case_by_id={c['case_id']:c for c in cases};resp_by_id={r['trial_id']:r for r in responses};assert len(resp_by_id)==96
 with zipfile.ZipFile(a.source_archive) as z:
  gallery=json.loads(z.read('GALLERY_SELECTED.json'))
  dispositions=json.loads(z.read('capture/DATASET_DISPOSITIONS.json'))
  selected=next(d for d in dispositions if d['bench']=='winogrande' and d['split']=='validation')
  raw_source=gzip.decompress(z.read('capture/'+selected['rows_file']))
  hs_source_record=next(d for d in dispositions if d['bench']=='hellaswag' and d['split']=='validation')
  hs_source_bytes=gzip.decompress(z.read('capture/'+hs_source_record['rows_file']))
  assert digest(hs_source_bytes)==hs_source_record['rows_sha256']
  hs_source=[json.loads(x) for x in hs_source_bytes.splitlines()]
 assert digest(raw_source)==selected['rows_sha256']=='69f3d7f3a900d775339b04c7de672609c40fca573e50f594f2ae66d8782505be'
 source=[json.loads(x) for x in raw_source.splitlines()];assert len(source)==1267
 entry=next(b for b in gallery['benches'] if b['bench_name']=='winogrande')
 contract=copy.deepcopy(entry['meta']['evaluation']);contract_before=compact(contract)
 pinned_modules=json.loads((a.support_dir/'UPSTREAM_SOURCES.json').read_text())
 assert pinned_modules['commit']==REV
 authenticated_modules=[]
 for pinned in pinned_modules['files']:
  local=a.support_dir/pinned['path']
  if not local.exists():continue
  raw=local.read_bytes()
  assert digest(raw)==pinned['sha256']
  assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==pinned['git_blob_sha']
  authenticated_modules.append(pinned)
 sys.path.insert(0,str(a.support_dir))
 import one_eval.metrics.common.general
 from one_eval.core.state import BenchInfo
 from one_eval.metrics.runner import MetricRunner as Runner
 prep=preprocessor(a.preprocessor)
 source_checks=[];cohorts={};source_gold=[]
 for i,row in enumerate(source):
  assert str(row['answer']) in ('1','2');source_gold.append(chr(64+int(row['answer'])))
 source_counts=dict(Counter(source_gold))
 for req in manifest:
  case=case_by_id[req['case_id']]
  if case['bench']!='winogrande':continue
  row=source[case['row_index']];assert row==case['source_row'];assert sha_obj(row)==case['source_row_sha256']
  assert case['displayed_choices']==[row['option1'],row['option2']]
  assert case['gold_letter']==chr(64+int(row['answer']))
  resp=resp_by_id[req['trial_id']]
  assert req['request_payload']==resp['request_payload'] and sha_obj(req['request_payload'])==req['request_sha256']==resp['request_sha256']
  assert req['request_payload']['input']==case['prompt']
  output=resp.get('output_text') or ''
  assert digest(output.encode())==resp['output_text_sha256']
  parsed=parse_final(output) if resp.get('completed_nonempty') else None
  source_checks.append(dict(trial_id=req['trial_id'],case_id=case['case_id'],source_row_index=case['row_index'],
      source_row_sha256=case['source_row_sha256'],request_sha256=req['request_sha256'],output_sha256=resp['output_text_sha256'],
      model=req['request_payload']['model'],gold_letter=case['gold_letter'],parsed_final=parsed,
      completed=bool(resp.get('completed_nonempty')),semantic_correct=None if parsed is None else parsed==case['gold_letter']))
  cohorts.setdefault(req['request_payload']['model'],[]).append((case,resp,parsed))
 reports=[];all_witnesses=[];healthy_controls=[]
 with tempfile.TemporaryDirectory() as tmp:
  tmp=Path(tmp)
  def run(native_rows,label,ref_key,metric_contract):
   assert compact(metric_contract)==contract_before,'Parser/contract mutated'
   path=tmp/(label+'.jsonl');path.write_text(''.join(compact(r)+'\n' for r in native_rows))
   bench=BenchInfo(bench_name='winogrande',meta={'artifact_paths':{'records':str(path)},'pred_key':'generated_ans','ref_key':ref_key})
   result=Runner(max_workers=2).run_bench_with_contract(bench,metric_contract)
   assert compact(metric_contract)==contract_before
   return result['primary_metric_result'],result['primary_metric_artifacts']['parse_results']
  def score_group(rows,label):
   mapping=copy.deepcopy(entry['meta']['key_mapping'])
   frame,mapping=prep._preprocess_dataframe(pd.DataFrame(rows),'winogrande',mapping,eval_type=entry['bench_dataflow_eval_type'])
   native=frame.to_dict('records')
   for nr,row in zip(native,rows):
    nr['_source_canonical_gold']='<answer>'+chr(64+int(row['answer']))+'</answer>'
   original_snapshot=sha_obj(native)
   original,parses=run(native,label+'_original',mapping['input_label_key'],copy.deepcopy(contract))
   fixed,fixparses=run(native,label+'_refkey_only','_source_canonical_gold',copy.deepcopy(contract))
   assert sha_obj(native)==original_snapshot,'Rows/predictions changed during ref-key intervention'
   value_only=copy.deepcopy(native)
   for row in value_only:row[mapping['input_label_key']]=row['_source_canonical_gold']
   value_score,value_parses=run(value_only,label+'_refvalue_only',mapping['input_label_key'],copy.deepcopy(contract))
   assert fixed['score']==value_score['score']
   for before,after in zip(native,value_only):
    assert [k for k in before if before[k]!=after[k]]==[mapping['input_label_key']]
   assert [p['pred'] for p in parses]==[p['pred'] for p in fixparses]==[p['pred'] for p in value_parses]
   return dict(n=len(rows),original=original,reference_key_only=fixed,reference_value_only=value_score,
               original_reference_parse_counts=dict(Counter(p['ref']['normalized'] for p in parses)),
               corrected_reference_parse_counts=dict(Counter(p['ref']['normalized'] for p in fixparses)),
               rows_and_prediction_snapshot_sha256=original_snapshot),parses,fixparses
  for model,trials in sorted(cohorts.items()):
   assert len(trials)==12
   base=[]
   for case,resp,parsed in trials:
    row=copy.deepcopy(case['source_row']);row['generated_ans']=resp.get('output_text') or '';base.append(row)
   result,origpars,fixedpars=score_group(base,model)
   const=copy.deepcopy(base)
   for row in const:row['generated_ans']='<answer>B</answer>'
   constant,_,_=score_group(const,model+'_constant_B')
   correct=sum(parsed==case['gold_letter'] for case,resp,parsed in trials if parsed is not None)
   unknown=sum(parsed is None for case,resp,parsed in trials)
   assert result['original']['score']==0.5 and constant['original']['score']==1.0
   assert correct/12>constant['reference_key_only']['score']==0.5
   assert result['reference_key_only']['score']==correct/12
   reports.append(dict(model=model,source_questions=12,known_correct=correct,unknown=unknown,
      corrected_semantic_bounds=[correct/12,(correct+unknown)/12],model_result=result,
      constant_B_result=constant,robust_model_vs_constant_reversal=True))
   for (case,resp,parsed),before,after in zip(trials,origpars,fixedpars):
    all_witnesses.append(dict(case_id=case['case_id'],model=model,source_row_index=case['row_index'],
       question=case['source_row']['sentence'],choices=case['displayed_choices'],raw_source_answer=case['source_row']['answer'],
       raw_output=resp.get('output_text'),source_gold=case['gold_letter'],native_parse=before,reference_only_parse=after))
  full=[]
  for predictor in ['oracle','constant_B']:
   rows=copy.deepcopy(source)
   for row,gold in zip(rows,source_gold):row['generated_ans']='<answer>'+(gold if predictor=='oracle' else 'B')+'</answer>'
   result,_,_=score_group(rows,'full_'+predictor);full.append(dict(predictor=predictor,result=result))
  assert full[0]['result']['original']['score']==639/1267
  assert full[1]['result']['original']['score']==1.0
  assert full[0]['result']['reference_key_only']['score']==1.0
  assert full[1]['result']['reference_key_only']['score']==639/1267
  # Healthy zero-based source control: same original HellaSwag contract, outputs,
  # and parser, with only a source-canonical reference column selected.
  he=next(b for b in gallery['benches'] if b['bench_name']=='hellaswag')
  hc=copy.deepcopy(he['meta']['evaluation']);hc_hash=sha_obj(hc)
  for model in sorted(cohorts):
   hs=[req for req in manifest if req['bench']=='hellaswag' and req['request_payload']['model']==model]
   assert len(hs)==12
   hrows=[]
   for req in hs:
    case=case_by_id[req['case_id']];row=copy.deepcopy(case['source_row'])
    assert row==hs_source[case['row_index']] and sha_obj(row)==case['source_row_sha256']
    assert case['gold_letter']==chr(65+int(row['label']))
    resp=resp_by_id[req['trial_id']]
    assert req['request_payload']==resp['request_payload']
    assert sha_obj(req['request_payload'])==req['request_sha256']==resp['request_sha256']
    row['generated_ans']=resp.get('output_text') or ''
    assert digest(row['generated_ans'].encode())==resp['output_text_sha256']
    row['_source_canonical_gold']='<answer>'+case['gold_letter']+'</answer>';hrows.append(row)
   hm=copy.deepcopy(he['meta']['key_mapping'])
   hf,hm=prep._preprocess_dataframe(pd.DataFrame(hrows),'hellaswag',hm,eval_type=he['bench_dataflow_eval_type'])
   hn=hf.to_dict('records');hp=tmp/(model+'_healthy_hellaswag.jsonl')
   hp.write_text(''.join(compact(r)+'\n' for r in hn))
   outcomes=[]
   for refkey in [hm['input_label_key'],'_source_canonical_gold']:
    hb=BenchInfo(bench_name='hellaswag',meta={'artifact_paths':{'records':str(hp)},'pred_key':'generated_ans','ref_key':refkey})
    hr=Runner(max_workers=2).run_bench_with_contract(hb,hc)
    assert sha_obj(hc)==hc_hash
    outcomes.append(hr['primary_metric_result'])
   assert outcomes[0]['score']==outcomes[1]['score']==11/12
   assert outcomes[0]['scored_samples']==outcomes[1]['scored_samples']==12
   healthy_controls.append(dict(benchmark='hellaswag',model=model,source_questions=12,
     original=outcomes[0],reference_only=outcomes[1],metric_contract_unchanged=True,
     metric_contract_sha256=hc_hash))
 code_receipts={str(p.relative_to(a.support_dir)):digest(p.read_bytes()) for p in a.support_dir.rglob('*.py') if '__pycache__' not in str(p)}
 origins={name:str(Path(sys.modules[name].__file__).resolve()) for name in [
   'one_eval.core.state','one_eval.core.metric_registry','one_eval.metrics.runner',
   'one_eval.metrics.common.general','one_eval.metrics.parsers.choice','one_eval.metrics.parsers.base']}
 assert all(Path(origin).is_relative_to(a.support_dir.resolve()) for origin in origins.values())
 out=dict(status='PASS_REFERENCE_ONLY_CONSEQUENCE',oneeval_commit=REV,model_archive_sha256=MODEL_SHA,source_archive_sha256=SOURCE_SHA,
  model_source_questions=12,model_outputs_reused=24,new_model_calls=0,new_judge_calls=0,
  native_original_parser=contract['parser'],native_original_parser_sha256=sha_obj(contract['parser']),
  native_full_evaluation_contract_sha256=sha_obj(contract),all_metric_contracts_unchanged=True,
  reference_key_only_rows_and_outputs_unchanged=True,reference_value_only_changed_field='answer',
  source_validation_rows=1267,source_gold_counts=source_counts,models=reports,full_source_constructed_controls=full,
  healthy_hellaswag_controls=healthy_controls,healthy_control_source_sha256=hs_source_record['rows_sha256'],
  healthy_model_outputs_reused=24,
  module_sha256=code_receipts,authenticated_module_sources=authenticated_modules,native_module_origins=origins,
  preprocessor_sha256=digest(a.preprocessor.read_bytes()),
  boundaries=['Validation split explicitly selected; shipped gallery default test has unavailable gold.',
    'Model responses used intended source-rendered prompts outside full native generation; this proof concerns scoring the same captured responses.',
    'Ordinary unmodified native metric/parser/runner/BenchInfo imports; only preprocessing class AST isolates unrelated provider dependencies.',
    'Gallery is marked reference_mapped and smoke_passed=false; no deployed or published third-party leaderboard claim.',
    'Full1267 oracle and constant predictions are constructed controls, not model inference.'])
 for name,obj in [('RESULT.json',out),('MODEL_SOURCE_IDENTITY.json',source_checks),('WITNESSES.json',all_witnesses)]:
  (a.out_dir/name).write_text(json.dumps(obj,indent=2,ensure_ascii=False)+'\n')
 print(json.dumps({'status':out['status'],'models':[{k:r[k] for k in ['model','known_correct','unknown','robust_model_vs_constant_reversal']} for r in reports],
    'full1267':[{ 'predictor':r['predictor'],'original':r['result']['original']['score'],'reference_only':r['result']['reference_key_only']['score']} for r in full],
    'parser_sha256':out['native_original_parser_sha256']},indent=2))

if __name__=='__main__':main()
