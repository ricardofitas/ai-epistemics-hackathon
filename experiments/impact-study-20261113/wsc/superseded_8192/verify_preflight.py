#!/usr/bin/env python3
"""Check source/split/payload geometry without candidate inference."""
import argparse,collections,hashlib,json,importlib.util
from pathlib import Path

def load(p):return json.loads(p.read_text())
def canonical(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('directory',type=Path,nargs='?',default=Path(__file__).resolve().parent);a=ap.parse_args();p=a.directory
 spec=importlib.util.spec_from_file_location('wsc_builder_for_preflight',p/'build_experiment.py');builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
 d=load(p/'selected_data.json');key=load(p/'task_key.json')['rows'];jobs=[json.loads(x) for x in (p/'manifest.jsonl').read_text().splitlines()];protocol=load(p/'protocol.json');split=load(p/'source_split.json')
 bypid={r['passage_id']:r for r in d['items']};tasks={r['task_id']:r for r in key};assert len(bypid)==len(d['items'])>=40;assert len(tasks)==len(key)==2*len(bypid)
 assert not set(split['prior_discovery_family_exclusions'])&{r['source_review_id'] for r in d['items']}
 assert len(jobs)==len({r['trial_id'] for r in jobs})
 assert sorted(r['execution_order'] for r in jobs)==list(range(1,len(jobs)+1))
 families=collections.defaultdict(set)
 for r in d['items']:families[r['family_id']].add(r['analysis_role'])
 assert all(len(v)==1 for v in families.values());assert len(families)==d['source_families']
 for pid in bypid:assert {r['variant'] for r in key if r['passage_id']==pid}=={'gold','non_gold'}
 model_tasks=collections.defaultdict(list);batches=collections.defaultdict(dict)
 for j in jobs:
  pay=j['request_payload'];assert j['request_sha256']==hashlib.sha256(canonical(pay)).hexdigest()
  assert pay['instructions']==builder.INSTRUCTION
  assert pay['model']==j['requested_model'] and pay['stream'] is True and pay['temperature']==0.0 and pay['max_output_tokens']==8192
  assert pay['tools']==[] and pay['tool_choice']=='none' and pay['store'] is False and pay['agentic_memory'] is False and 'previous_response_id' not in pay
  inp=json.loads(pay['input']);assert len(inp)==len(j['task_ids'])==len({r['id'] for r in inp});assert {r['id'] for r in inp}==set(j['task_ids']);assert all(set(r)=={'id','premise','hypothesis'} for r in inp)
  assert len(j['task_ids'])==len(set(j['task_ids']))<=8
  assert len({tasks[t]['analysis_role'] for t in j['task_ids']})==1
  assert {tasks[t]['analysis_role'] for t in j['task_ids']}=={j['batch_role']}
  assert len(j['task_ids'])==2*len(j['passage_ids'])
  assert len(j['passage_ids'])==len(set(j['passage_ids']))
  assert {tasks[t]['passage_id'] for t in j['task_ids']}==set(j['passage_ids'])
  for pid in j['passage_ids']:assert sorted(tasks[t]['variant'] for t in j['task_ids'] if tasks[t]['passage_id']==pid)==['gold','non_gold']
  assert j['batch_index'] not in batches[pay['model']]
  for inp_row in inp:
   t=tasks[inp_row['id']];source=bypid[t['passage_id']]
   assert inp_row['premise']==source['premise'] and inp_row['hypothesis']==source[t['variant']+'_replacement_hypothesis']
  model_tasks[pay['model']].extend(j['task_ids']);batches[pay['model']][j['batch_index']]=(j['task_ids'],j['batch_role'])
 assert set(model_tasks)==set(protocol['models']) and len(model_tasks)==4
 for values in model_tasks.values():assert len(values)==len(set(values))==len(tasks) and set(values)==set(tasks)
 reference=batches[protocol['models'][0]]
 assert all(v==reference for v in batches.values())
 assert len(jobs)==protocol['request_plan']['requests'] and len(key)*4==protocol['request_plan']['ordered_classifications_total']
 assert protocol['models']==['gemma-4-31b-it','glm-5.2','qwen3.8-27b','deepseek-v4-flash']
 for name,value in protocol['hashes'].items():assert hashlib.sha256((p/name).read_bytes()).hexdigest()==value,name
 assert hashlib.sha256((p/protocol['final_semantic_eligibility_filename']).read_bytes()).hexdigest()==protocol['final_semantic_eligibility_sha256']
 approval=load(p/'ROOT_SEMANTIC_APPROVAL.json');freeze=load(p/'semantic_ab_freeze.json');semantic=load(p/protocol['final_semantic_eligibility_filename'])
 assert approval['status']=='approved_for_prospective_execution_after_separate_git_freeze'
 assert approval['input_semantic_final_sha256']==protocol['final_semantic_eligibility_sha256']
 assert approval['first_a_sha256']==hashlib.sha256((p/'semantic_first_a.jsonl').read_bytes()).hexdigest()
 assert approval['first_b_sha256']==hashlib.sha256((p/'semantic_first_b.jsonl').read_bytes()).hexdigest()
 assert freeze['semantic_packet_sha256']==hashlib.sha256((p/'semantic_review_packet.jsonl').read_bytes()).hexdigest()
 assert freeze['first_sha256']=={'a':approval['first_a_sha256'],'b':approval['first_b_sha256']}
 assert semantic['semantic_first_freeze_sha256']==hashlib.sha256((p/'semantic_ab_freeze.json').read_bytes()).hexdigest()
 assert hashlib.sha256((p/'analyze_wsc.py').read_bytes()).hexdigest()==protocol['analysis_sha256']
 assert hashlib.sha256((p.parent/'methods/capture_audit_source.py').read_bytes()).hexdigest()==protocol['capture_audit_source_sha256']
 assert hashlib.sha256((p.parent/'methods/run_adaption_stream_pilot.py').read_bytes()).hexdigest()==protocol['runner_sha256']
 print(json.dumps({'status':'PASS','source_passages':len(bypid),'source_families':len(families),'requests':len(jobs),'ordered_classifications':len(key)*4,'split':dict(collections.Counter(r['analysis_role'] for r in d['items'])),'all_four_model_task_coverage':True,'model_payload_keys_only':['id','premise','hypothesis'],'prior_witness_family_absent':True,'no_inference':True}))
if __name__=='__main__':main()
