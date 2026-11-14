"""Independent, no-network verification of the frozen 160-request artifact.

Does not import either production analysis module. The exact pinned official
free-form parser is evaluated independently via its verified function ASTs.
"""
from __future__ import annotations
import argparse, ast, collections, datetime, decimal, hashlib, itertools, json, pathlib, re
from types import SimpleNamespace

EXPECTED_PROTOCOL = 'b148003b2fb83cb4977a873851409f0068e70307b1ecab624073d7c59feb6e15'
EXPECTED_MANIFEST = '7ab4c169492f9bfa2cff12e838e9972eb219d2067feea1c1ec3ee5b1ec608e43'
EXPECTED_SCORER = '85077e61ca01f4c240158ff3b18a0451130fa879a2a46a11f3b382dbbf1fd73a'
EXPECTED_COMMIT = '3faed45df0d53d97f0a47c3517719864a8d23007'
EXPECTED_PROTOCOL_COMMIT = 'ddedfcd6c2f2633b6e1460f8591ce5ed261959d7'
EXPECTED_RUN = 43615821403
CONDITIONS = ('free_form__absent', 'free_form__A.None', 'choice__absent', 'choice__A.None')
CONTRASTS = {
 'instruction_freeform_minus_choice_at_absent': (1,0,-1,0),
 'instruction_freeform_minus_choice_at_present': (0,1,0,-1),
 'carrier_absent_minus_present_at_freeform': (1,-1,0,0),
 'carrier_absent_minus_present_at_choice': (0,0,1,-1),
 'interaction_instruction_gain_absent_minus_present': (1,-1,-1,1),
}
def canonical(x): return json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
def sha(x): return hashlib.sha256(x).hexdigest()
def objhash(x): return sha(canonical(x))
def read(path): return json.loads(path.read_text())
def jsonl(path): return [json.loads(l) for l in path.read_text().splitlines() if l.strip()] if path.exists() else []
def extract_text(response):
 parts=[]
 for item in response.get('output',[]) or []:
  if isinstance(item,dict) and item.get('type')=='message' and item.get('role','assistant')=='assistant':
   parts += [c['text'] for c in item.get('content',[]) if isinstance(c,dict) and c.get('type')=='output_text' and isinstance(c.get('text'),str)]
 return '\n'.join(parts)
def official_rules(root):
 import numpy as np
 path=root/'official/mix_eval/utils/metric_utils.py'; assert sha(path.read_bytes())==EXPECTED_SCORER
 wanted={'check_is_number','normalize_str','extract_numbers','parse_freeform_response_rule','eval_freeform_rule'}
 nodes=[n for n in ast.parse(path.read_text()).body if isinstance(n,ast.FunctionDef) and n.name in wanted]
 assert {n.name for n in nodes}==wanted
 env={'re':re,'np':np};exec(compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),str(path),'exec'),env)
 def score(record,text):
  parsed=env['parse_freeform_response_rule'](SimpleNamespace(model_type='APIModelBase'),text)
  return float(env['eval_freeform_rule'](record['target'],parsed)),parsed
 return score
def conservative(values, coefficients):
 # Deliberately compute all possible assignments to the at-most-four unknown
 # cells, independently of the production coefficient-sign accumulation.
 possible=[(v,) if v is not None else (0,1) for v in values]
 sums=[sum(c*v for c,v in zip(coefficients,assignment)) for assignment in itertools.product(*possible)]
 return min(sums),max(sums)
def effects(scores, cases, models):
 result={}
 for model in models:
  counts={c:{'planned':20,'known_correct':0,'known_incorrect':0,'unknown':0} for c in CONDITIONS}
  for case in cases:
   for c in CONDITIONS:
    value=scores[(model,case,c)];counts[c]['unknown' if value is None else 'known_correct' if value==1 else 'known_incorrect']+=1
  estimates={}
  for name,coeff in CONTRASTS.items():
   bounds=[conservative([scores[(model,case,c)] for c in CONDITIONS],coeff) for case in cases]
   estimates[name]={'lower':sum(x[0] for x in bounds)/20,'upper':sum(x[1] for x in bounds)/20}
  result[model]={'source_cases':20,'counts':counts,'contrasts':estimates}
 return result

def verify(root, score_function=None):
 root=pathlib.Path(root).resolve(); errors=[]; warnings=[]
 def check(ok, reason, tid=None):
  if not ok:errors.append({'error':reason,**({'trial_id':tid} if tid else {})})
 def warn(reason,tid=None):warnings.append({'warning':reason,**({'trial_id':tid} if tid else {})})
 protocol=read(root/'PROTOCOL.json');launch=read(root/'LAUNCH.json')
 check(sha((root/'PROTOCOL.json').read_bytes())==EXPECTED_PROTOCOL==launch.get('protocol_sha256'),'protocol_identity')
 check(sha((root/'manifest.jsonl').read_bytes())==EXPECTED_MANIFEST==launch.get('manifest_sha256'),'manifest_identity')
 check(launch.get('protocol_commit')==EXPECTED_PROTOCOL_COMMIT,'prelaunch_protocol_commit')
 for name,digest in protocol['frozen_files'].items():check(sha((root/name).read_bytes())==digest,'frozen_file:'+name)
 manifest=jsonl(root/'manifest.jsonl');prepared=jsonl(root/'PREPARED_MANIFEST.jsonl');cases=read(root/'selected20.json')
 check(len(manifest)==len(prepared)==160 and len(cases)==20,'fixed_design_size')
 plans={r['trial_id']:r for r in manifest};source={r['source_index']:r for r in cases};models=sorted(protocol['models'])
 check(len(plans)==160 and len(source)==20 and len(models)==2,'design_uniqueness')
 check(protocol.get('maximum_requests')==160 and protocol.get('attempts_per_request')==1 and protocol.get('retry') is False,'attempt_cap')
 check(protocol.get('maximum_output_tokens_total')==655360,'total_output_cap')
 check({(r['source_index'],r['request_payload']['model'],r['condition']) for r in manifest}==set(itertools.product(source,models,CONDITIONS)),'all_factorial_cells')
 flags={'stream':True,'tools':[],'tool_choice':'none','store':False,'agentic_memory':False}
 positions=collections.Counter()
 for i,(r,original) in enumerate(zip(manifest,prepared)):
  payload=r['request_payload'];case=source[r['source_index']]
  check(objhash(case['record'])==case['source_sha256']==r['source_sha256'],'source_identity',r['trial_id'])
  check(objhash(payload)==r['request_sha256'],'wire_request_identity',r['trial_id'])
  check(sha(payload['input'].encode())==r['prompt_sha256'],'prompt_identity',r['trial_id'])
  check(payload['model'] in models and payload['temperature']==0 and payload['max_output_tokens']==4096 and len(payload['input'].encode())<=8192,'wire_caps',r['trial_id'])
  stripped={k:v for k,v in payload.items() if k not in flags};derived=dict(r);derived['request_payload']=stripped;derived['request_sha256']=objhash(stripped)
  check(derived==original and payload=={**original['request_payload'],**flags},'transport_only_derivation',r['trial_id'])
 # Cell balance is checked independently from the actual source/model-local
 # serial occurrence position, not inferred from labels or the producer code.
 for model in models:
  for case in source:
   ordered=[r for r in manifest if r['source_index']==case and r['request_payload']['model']==model]
   for pos,r in enumerate(ordered):positions[(model,r['condition'],pos)]+=1
 check(all(positions[(m,c,p)]==5 for m in models for c in CONDITIONS for p in range(4)),'counterbalance_positions')
 index=read(root/'ARTIFACT_INDEX.json');check(index.get('credential_scan_passed') is True,'credential_scan_marker')
 indexed=set()
 for entry in index['files']:
  target=(root/entry['path']).resolve();check(target.is_relative_to(root),'artifact_index_path_escape')
  if target.is_relative_to(root):check(target.is_file() and sha(target.read_bytes())==entry['sha256'],'artifact_index_hash:'+entry['path'])
  indexed.add(entry['path'])
 ledger=jsonl(root/'CALL_LEDGER.jsonl');starts=[r for r in ledger if r.get('event')=='attempt_started'];recorded=[r for r in ledger if r.get('event')=='attempt_recorded']
 check(len(starts)<=160 and len({x.get('trial_id') for x in starts})==len(starts),'attempt_start_uniqueness_cap')
 check([x.get('trial_id') for x in starts]==[r['trial_id'] for r in manifest[:len(starts)]],'attempt_order')
 check(len({x.get('trial_id') for x in recorded})==len(recorded),'attempt_record_uniqueness')
 startmap={x['trial_id']:x for x in starts};recordmap={x['trial_id']:x for x in recorded}
 check(set(recordmap)<=set(startmap),'record_without_start')
 for e in starts:check(e.get('attempt_count')==1 and e.get('request_sha256')==plans[e['trial_id']]['request_sha256'],'attempt_event_identity',e['trial_id'])
 times=[datetime.datetime.fromisoformat(x['utc'].replace('Z','+00:00')) for x in starts]
 intervals=[(b-a).total_seconds() for a,b in zip(times,times[1:])]
 check(not intervals or min(intervals)>=4.99,'minimum_start_cadence_5sec_with_10ms_rounding')
 aggregate=jsonl(root/'responses.jsonl');aggregate_map={x['trial_id']:x for x in aggregate}
 check(len(aggregate_map)==len(aggregate),'aggregate_unique_ids');check(set(aggregate_map)<=set(startmap),'aggregate_unattempted_ids')
 paths={p.stem:p for p in (root/'api_artifacts').glob('*.json')};check(set(paths)<=set(startmap),'artifact_unattempted_ids')
 check(set(paths)<=set(plans),'unexpected_artifact_id')
 receipts={tid:read(path) for tid,path in paths.items()}
 provider_id_slots=collections.defaultdict(list)
 for tid,receipt in receipts.items():
  if isinstance(receipt,dict) and receipt.get('response_id'):provider_id_slots[receipt['response_id']].append(tid)
 duplicate_slots={tid for slots in provider_id_slots.values() if len(slots)>1 for tid in slots}
 response_ids={};scores={};observations=[];usage_input=usage_output=usage_records=0;cost=decimal.Decimal(0);statuses=collections.Counter();terminal_kinds=collections.Counter()
 score_function=score_function or official_rules(root)
 for row in manifest:
  tid=row['trial_id'];key=(row['request_payload']['model'],row['source_index'],row['condition']);score=None;parsed=None;why=[];receipt=receipts.get(tid)
  before=len(errors)
  if receipt is None:
   why.append('unattempted' if tid not in startmap else 'attempted_missing_artifact')
  elif not isinstance(receipt,dict):check(False,'nonobject_receipt',tid);why.append('invalid_receipt')
  else:
   check('api_artifacts/'+tid+'.json' in indexed,'receipt_not_in_final_index',tid)
   check(tid not in duplicate_slots,'duplicate_provider_response_id',tid)
   check(receipt.get('trial_id')==tid and receipt.get('attempt_count')==1,'receipt_attempt_identity',tid)
   if tid in aggregate_map:check(receipt==aggregate_map[tid],'aggregate_artifact_disagreement',tid)
   else:warn('artifact_missing_aggregate_record',tid)
   associated=True
   for field,expected in [('request_sha256',row['request_sha256']),('requested_model',row['request_payload']['model']),('returned_model',row['request_payload']['model'])]:
    if receipt.get(field) is None:associated=False;why.append('missing_'+field)
    else:check(receipt[field]==expected,'contradictory_'+field,tid)
   if receipt.get('request_payload') is None:associated=False;why.append('missing_request_payload')
   else:check(receipt['request_payload']==row['request_payload'] and objhash(receipt['request_payload'])==row['request_sha256'],'request_payload_identity',tid)
   text=receipt.get('output_text');textvalid=isinstance(text,str) and receipt.get('output_text_sha256')==sha(text.encode())
   if isinstance(text,str) and receipt.get('output_text_sha256') is not None:check(textvalid,'output_text_identity',tid)
   if not textvalid:why.append('missing_or_invalid_output_identity')
   rid=receipt.get('response_id')
   if rid:
    check(rid not in response_ids,'duplicate_provider_response_id',tid);response_ids[rid]=tid
   status=receipt.get('response_status');statuses[str(status)]+=1
   journalpath=root/'stream_journals'/(tid+'.jsonl');journal_ok=False
   if journalpath.exists():
    check('stream_journals/'+tid+'.jsonl' in indexed,'journal_not_in_final_index',tid)
    if receipt.get('stream_journal_sha256') is not None:check(sha(journalpath.read_bytes())==receipt['stream_journal_sha256'],'journal_hash',tid)
    else:why.append('missing_journal_hash')
    frames=jsonl(journalpath);terminal=[]
    for frame in frames:
     data=frame.get('data');kind=(data.get('type') if isinstance(data,dict) else None) or frame.get('event')
     if kind in {'response.completed','response.incomplete','response.failed','response.cancelled'} and not frame.get('partial_frame') and isinstance(data,dict) and isinstance(data.get('response'),dict):terminal.append((kind,data['response']))
    if terminal:
     kind,terminal_obj=terminal[-1];terminal_kinds[kind]+=1
     check(receipt.get('raw_response')==terminal_obj,'terminal_raw_object_identity',tid)
     check(receipt.get('terminal_event')==kind and receipt.get('terminal_event_seen') is True,'terminal_flags_identity',tid)
     check(terminal_obj.get('status')==status,'terminal_status_identity',tid)
     check(receipt.get('response_id')==terminal_obj.get('id') and receipt.get('returned_model')==terminal_obj.get('model'),'terminal_provider_identity',tid)
     check(receipt.get('usage')==terminal_obj.get('usage'),'terminal_usage_identity',tid)
     terminal_text=extract_text(terminal_obj)
     if not terminal_text and isinstance(terminal_obj.get('output_text'),str):terminal_text=terminal_obj['output_text']
     check(not textvalid or terminal_text==text,'terminal_text_identity',tid)
     journal_ok=receipt.get('stream_journal_sha256')==sha(journalpath.read_bytes())
    else:why.append('missing_terminal_object')
   else:why.append('missing_journal')
   if receipt.get('local_capture_error'):why.append('local_capture_error')
   if status!='completed':why.append('response_not_completed')
   complete=(associated and textvalid and journal_ok and receipt.get('completed_nonempty') is True and receipt.get('http_status')==200 and status=='completed' and not receipt.get('stream_incomplete') and not receipt.get('transport_error') and not receipt.get('api_error') and not receipt.get('local_capture_error') and bool(text.strip()))
   # Crucially, event name response.completed is not used to infer completed
   # response status: incomplete terminal objects remain unknown.
   if complete and len(errors)==before:score,parsed=score_function(source[row['source_index']]['record'],text)
   else:why.append('ineligible_capture')
   usage=receipt.get('usage')
   if isinstance(usage,dict) and all(type(usage.get(k)) is int and usage[k]>=0 for k in ['input_tokens','output_tokens']):
    usage_records+=1;usage_input+=usage['input_tokens'];usage_output+=usage['output_tokens'];check(usage['output_tokens']<=4096,'provider_output_token_cap',tid)
    if usage.get('cost') is not None:
     try:
      units=decimal.Decimal(str(usage['cost']));assert units.is_finite() and units>=0;cost+=units
     except (decimal.InvalidOperation,ValueError,AssertionError):check(False,'invalid_cost_units',tid)
   else:warn('usage_missing_or_invalid',tid)
   if tid not in recordmap:warn('attempt_recorded_event_missing',tid)
   else:
    event=recordmap[tid];check(event.get('usage')==(receipt.get('usage') or {}) and event.get('http_status')==receipt.get('http_status') and event.get('completed_nonempty')==receipt.get('completed_nonempty'),'recorded_event_receipt_identity',tid)
  if len(errors)>before:score=None;why.append('integrity_failure_unknown')
  scores[key]=score;observations.append({'trial_id':tid,'model':key[0],'source_index':key[1],'condition':key[2],'score':score,'parsed':parsed,'reasons':why})
 check(usage_output<=655360,'aggregate_output_token_cap')
 inferred=effects(scores,list(source),models)
 comparison='NOT_AVAILABLE';summarypath=root/'analysis/ANALYSIS_SUMMARY.json'
 if summarypath.exists():
  claimed=read(summarypath);check(claimed['planned_requests']==160 and claimed['completed_scored']==sum(x['score'] is not None for x in observations),'analysis_completion_counts')
  check(claimed['input_tokens']==usage_input and claimed['output_tokens']==usage_output and decimal.Decimal(claimed['cost_units'])==cost,'analysis_usage_totals')
  for m in models:
   check(claimed['factorial']['models'][m]['counts']==inferred[m]['counts'],'analysis_cell_counts:'+m)
   for contrast,bounds in inferred[m]['contrasts'].items():
    check(all(claimed['factorial']['models'][m]['contrasts'][contrast][k]==bounds[k] for k in ['lower','upper']),'analysis_contrast:'+m+':'+contrast)
  comparison='PASS' if not any(x['error'].startswith('analysis_') for x in errors) else 'FAIL'
 execution=read(root/'EXECUTION_RECEIPT.json') if (root/'EXECUTION_RECEIPT.json').exists() else None
 if execution:
  check(str(execution.get('run_id'))==str(EXPECTED_RUN) and execution.get('execution_commit')==EXPECTED_COMMIT,'execution_run_commit')
  check(execution.get('recorded')==len(aggregate) and execution.get('manifest_sha256')==EXPECTED_MANIFEST,'execution_record_count_manifest')
 final=read(root/'FINAL_CAPTURE_STATUS.json') if (root/'FINAL_CAPTURE_STATUS.json').exists() else None
 if final:check(final.get('planned')==160 and final.get('recorded')==len(aggregate) and final.get('unattempted')==160-len(aggregate),'final_fixed_slots')
 else:warn('final_capture_status_missing_interrupted_run')
 return {'status':'PASS' if not errors else 'FAIL','expected_run_id':EXPECTED_RUN,'expected_launch_commit':EXPECTED_COMMIT,'planned':160,'source_questions':20,'models':models,'attempt_started':len(starts),'attempt_recorded':len(recorded),'per_trial_artifacts':len(paths),'aggregate_records':len(aggregate),'completed_scored':sum(x['score'] is not None for x in observations),'unknown':sum(x['score'] is None for x in observations),'minimum_start_interval_seconds':min(intervals) if intervals else None,'usage_records':usage_records,'input_tokens':usage_input,'output_tokens':usage_output,'cost_units':str(cost),'cost_currency':None,'response_statuses':dict(statuses),'terminal_event_kinds':dict(terminal_kinds),'analysis_comparison':comparison,'effects':inferred,'errors':errors,'warnings':warnings,'new_model_or_judge_calls':0,'boundary':'Independent source/manifest/terminal/ledger/officialRULE/exhaustive-unknown-assignment verification of captured artifacts; not independent provider authentication or new model experiment.'},observations

def main():
 ap=argparse.ArgumentParser();ap.add_argument('artifact_directory',type=pathlib.Path);ap.add_argument('--output',type=pathlib.Path,default=pathlib.Path(__file__).parent/'FINAL_VERIFICATION.json');args=ap.parse_args()
 try:report,rows=verify(args.artifact_directory)
 except Exception as e:
  report={'status':'FAIL','fatal_error':type(e).__name__,'detail':str(e),'new_model_or_judge_calls':0};rows=[]
 args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n');args.output.with_name('INDEPENDENT_SCORES.json').write_text(json.dumps(rows,indent=2,ensure_ascii=False)+'\n')
 print(json.dumps({k:report.get(k) for k in ['status','planned','completed_scored','unknown','analysis_comparison','fatal_error']}));return 0 if report['status']=='PASS' else 1
if __name__=='__main__':raise SystemExit(main())
