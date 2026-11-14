"""Isolated fault-path test; no provider, dataset, model output or live result read."""
import importlib.util,json,sys,tempfile,types,shutil
from pathlib import Path
P=Path(__file__).resolve().parent
adapter=types.ModuleType('scoring_adapter')
def forbidden(*args,**kwargs):raise RuntimeError('Scorer must never run in these missing-capture tests')
adapter.score_case=forbidden;sys.modules['scoring_adapter']=adapter
spec=importlib.util.spec_from_file_location('frozen_analysis',P/'audit_inputs/analyze_paired.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
rows=[dict(trial_id=f'{i}-{c}-{model}',source_index=i,condition=c,request_sha256='frozen-request-hash',request_payload={'model':model}) for i in range(20) for c in ['binding_only','official_typed'] for model in ['model_a','model_b']]
reports=[]
for kind in ['all_unattempted','emitted_local_capture_error','wrong_request_hash']:
 with tempfile.TemporaryDirectory() as td:
  root=Path(td);m.P=root
  (root/'manifest.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows))
  (root/'selected20.json').write_text(json.dumps([{'source_index':i,'record':{}} for i in range(20)]))
  if kind!='all_unattempted':
   (root/'api_artifacts').mkdir()
   # EXACT shape of execute_paired.py's exception receipt, not a model output.
   record={'trial_id':rows[0]['trial_id'],'attempt_count':1,'local_capture_error':'OSError','completed_nonempty':False}
   if kind=='wrong_request_hash':record['request_sha256']='wrong-hash'
   (root/'api_artifacts'/(rows[0]['trial_id']+'.json')).write_text(json.dumps(record))
  try:
   m.main();result=json.loads((root/'ANALYSIS_SUMMARY.json').read_text());status='completed'
  except Exception as exc:status=type(exc).__name__;result=None
  expected='completed_partial_with_unknown_capture' if kind!='wrong_request_hash' else 'integrity_failure'
  reports.append(dict(case=kind,expected=expected,actual=status,report=result))
assert reports[0]['actual']=='completed'
assert reports[0]['report']['completed_scored']==0
assert all(e['gain_bounds']==[-1,1] for e in reports[0]['report']['effects'])
assert reports[1]['actual']=='AssertionError'
assert reports[2]['actual']=='AssertionError'
out={'status':'CONFIRMED_DIAGNOSTIC_MISMATCH','cases':reports,'meaning':'Frozen analyzer fails on an exception receipt the frozen executor can emit, instead of retaining that row as unknown. This is a fault-path reproduction, not evidence that the live run experienced a capture error. Wrong explicit request hash should remain an integrity failure.','models_called':0,'live_outputs_read':0,'suggested_followup':'Owner should preserve original files/results; independently classify local-capture-error receipts against manifest+attempt ledger, retain unknown score bounds, and document any post-launch analyzer fix before rerunning analysis only. Do not relaunch generation.'}
(P/'ANALYZER_FAULT_AUDIT.json').write_text(json.dumps(out,indent=2)+'\n');print(out['meaning'])
