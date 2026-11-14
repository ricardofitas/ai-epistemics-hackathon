"""Frozen common-scorer paired analysis; unknown outcomes retain bounds."""
from pathlib import Path
from decimal import Decimal
import hashlib,json,random
from scoring_adapter import score_case
P=Path(__file__).resolve().parent
canonical=lambda v:json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def main():
 manifest=[json.loads(x) for x in (P/'manifest.jsonl').read_text().splitlines()]
 cases={x['source_index']:x for x in json.loads((P/'selected20.json').read_text())}
 assert len(manifest)==80 and len(cases)==20
 outcomes=[];lookup={};cost=Decimal(0);usage_records=0;inp=out=0
 for row in manifest:
  tid=row['trial_id'];f=P/'api_artifacts'/(tid+'.json');r=json.loads(f.read_text()) if f.exists() else None
  score=None;reason='unattempted';judged=None
  if r:
   assert r['trial_id']==tid
   assert r.get('request_sha256')==row['request_sha256']
   if r.get('request_payload') is not None:assert hashlib.sha256(canonical(r['request_payload'])).hexdigest()==row['request_sha256']
   text=r.get('output_text')
   if isinstance(text,str):assert hashlib.sha256(text.encode()).hexdigest()==r['output_text_sha256']
   complete=(r.get('completed_nonempty') is True and r.get('http_status')==200 and r.get('response_status')=='completed' and not r.get('stream_incomplete') and not r.get('transport_error') and not r.get('api_error') and isinstance(text,str) and bool(text.strip()))
   if complete:
    judged=score_case(cases[row['source_index']]['record'],text,random.Random(42))
    if judged['status']=='PASS':score=judged['score'];reason='completed_scored'
    else:reason='scorer_incomplete'
   else:reason='capture_incomplete_or_empty'
   u=r.get('usage') or {}
   if all(type(u.get(k)) in (int,float) for k in ['input_tokens','output_tokens']):
    usage_records+=1;inp+=u['input_tokens'];out+=u['output_tokens'];assert u['output_tokens']<=4096
   if u.get('cost') is not None:cost+=Decimal(str(u['cost']))
  model=row['request_payload']['model'];key=(model,row['source_index'],row['condition']);assert key not in lookup
  item=dict(trial_id=tid,source_index=row['source_index'],model=model,condition=row['condition'],score=score,status=reason,judged=judged)
  lookup[key]=item;outcomes.append(item)
 models=sorted({r['request_payload']['model'] for r in manifest});effects=[]
 for model in models:
  low=high=0;complete=0;typed_win=binding_win=tie=0;raw=[]
  for i in cases:
   b=lookup[(model,i,'binding_only')]['score'];t=lookup[(model,i,'official_typed')]['score']
   low+=(0 if t is None else t)-(1 if b is None else b)
   high+=(1 if t is None else t)-(0 if b is None else b)
   if b is not None and t is not None:
    complete+=1;typed_win+=t>b;binding_win+=b>t;tie+=t==b
   raw.append(dict(source_index=i,binding_only=b,official_typed=t))
  effects.append(dict(model=model,pairs=20,complete_pairs=complete,typed_wins=typed_win,binding_wins=binding_win,ties=tie,gain_bounds=[low/20,high/20],pairs_detail=raw))
 report=dict(status='complete' if all(x['score'] is not None for x in outcomes) else 'partial',planned_requests=80,recorded_artifacts=sum((P/'api_artifacts'/(r['trial_id']+'.json')).exists() for r in manifest),completed_scored=sum(x['score'] is not None for x in outcomes),effects=effects,usage_records=usage_records,input_tokens=inp,output_tokens=out,cost_units=str(cost),cost_currency=None,scoring_mode='official_optional_rule_not_default_judge',new_judge_calls=0)
 (P/'ANALYSIS_CAPTURES.json').write_text(json.dumps(outcomes,indent=2,ensure_ascii=False)+'\n')
 (P/'ANALYSIS_SUMMARY.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
