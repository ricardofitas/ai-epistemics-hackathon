"""Exercise new gateway with authenticated old captures, never live transport."""
from pathlib import Path
import base64,copy,hashlib,json
from source_contract_gateway import SourceRegistry,TransportCapture,canonical_bytes,sha256
from check_contract import run_source_bound_evaluation
P=Path(__file__).resolve().parent;R=P.parent

def safe(v):
 if isinstance(v,bytes):return {'encoding':'base64','data':base64.b64encode(v).decode(),'sha256':sha256(v),'bytes':len(v)}
 if isinstance(v,dict):return {str(k):safe(x) for k,x in v.items()}
 if isinstance(v,(tuple,list)):return [safe(x) for x in v]
 return v

def main():
 selected=json.load(open(R/'real/selected2.json'));registry=SourceRegistry.from_selected(selected);rows=[]
 initial={str(p.relative_to(R)):sha256(p.read_bytes()) for folder in [R/'real',R/'rescore'] for p in folder.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
 for item in selected:
  case=item['source_index'];source=item['record'];key=(str(case),item['source_sha256'])
  for condition in ['native_gallery','source_typed']:
   d=R/'real/results/real'/f'{case}_{condition}';trace=json.load(open(d/'HTTP_TRACE.json'))[0];old=json.load(open(d/'RESULT.json'))
   raw_wire=json.dumps(trace['request_payload'],allow_nan=False).encode();raw_body=trace['response_body'].encode()
   assert sha256(raw_wire)==trace['request_sha256'];assert sha256(raw_body)==trace['body_sha256']
   previous_rescore=json.load(open(R/'rescore/results'/f'{case}_{condition}/RESULT.json'))
   metric_manifest={'kind':'Authenticated historical native MetricRunner RESULT replay; not a new installed invocation','native_origins':json.load(open(R/'rescore/RESCORE_SUMMARY.json'))['native_module_origins'],'evaluation':json.load(open(d/'BENCH.json'))['meta']['evaluation'],'pred_key':'provider_final_content','ref_key':'target'}
   scorer_hash=sha256(canonical_bytes(metric_manifest));calls=[];metric_calls=[]
   def transport(request):
    calls.append(request.request_sha256)
    return TransportCapture(trace['http_status'],raw_wire,raw_body,'Pinned original native HTTP_TRACE regression',method=trace['method'],url=trace['url'])
   def metric(row):
    metric_calls.append(sha256(canonical_bytes(row)))
    expected=json.loads((R/'rescore/results'/f'{case}_{condition}/records.jsonl').read_text())
    assert row==expected,'Gateway derivative must equal authenticated installed-rescore input'
    return copy.deepcopy(previous_rescore['rescored_metric_result'])
   report=run_source_bound_evaluation(registry,key,source,source['target'],transport,native_request_bytes=raw_wire,delivered_row=old['delivered_row'],original_native_result=old,metric_adapter=metric,scorer_sha256=scorer_hash)
   if condition=='source_typed':
    assert report['status']=='SCORED' and report['eligible_metric_score']==1 and len(calls)==len(metric_calls)==1
    assert report['provider_final_content']==json.loads(raw_body)['choices'][0]['message']['content']
    assert report['delivered_row']['generated_ans']==old['delivered_row']['generated_ans']
   else:assert report['status']=='INVALID' and calls==metric_calls==[] and report['failures']==['native_request_profile_mismatch']
   assert report['original_native_result']==old
   rows.append({'source_index':case,'condition':condition,'report':safe(report),'transport_callback_calls':len(calls),'metric_replay_callback_calls':len(metric_calls),'historical_native_zero_status':old.get('native_zero_interpretation'),'historical_rescore_metric':previous_rescore['rescored_metric_result'],'declared_scorer_manifest':metric_manifest})
 for rel,digest in initial.items():assert sha256((R/rel).read_bytes())==digest,rel
 result={'status':'PASS','stage':'Post-outcome engineering regression of newcode','source_questions_reused':2,'archived_http_requests':4,'typed_pass':2,'stock_known_request_faults_blocked':2,'new_provider_calls':0,'new_installed_metric_calls':0,'metric_callback_boundary':'Two authenticated historical installed-rescore results replayed after checking the complete derivative row against archivedrecords; this is not a new native MetricRunner invocation.','typed_transport_callbacks':2,'native_compatibility':'Optional installed runner adapter supplied by module but not installed/executed in this regression environment','original_extracted_files_unchanged':len(initial),'cases':rows}
 (P/'ARCHIVED_REGRESSION.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='cases'}))
if __name__=='__main__':main()
