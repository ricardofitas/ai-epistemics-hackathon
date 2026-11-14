"""Offline factorial bounds from verified scores. Missing records remain unknown."""
import argparse,collections,json,pathlib
ROOT=pathlib.Path(__file__).resolve().parent
def analyze(scores):
 manifest=[json.loads(l) for l in (ROOT/'manifest.jsonl').read_text().splitlines()];plans={r['trial_id']:r for r in manifest};byid={}
 for row in scores:
  tid=row['trial_id']
  if tid not in plans or tid in byid:raise ValueError('unknown_or_duplicate_trial_id')
  if row['request_sha256']!=plans[tid]['request_sha256']:raise ValueError('request_identity_mismatch')
  value=row.get('score')
  if value not in (None,0,1) or type(value) is bool:raise ValueError('score_must_be_0_1_or_null')
  if value is not None and row.get('verified_complete') is not True:raise ValueError('unverified_score')
  byid[tid]=value
 functions={
  'instruction_freeform_minus_choice_at_absent':{'free_form__absent':1,'choice__absent':-1},
  'instruction_freeform_minus_choice_at_present':{'free_form__A.None':1,'choice__A.None':-1},
  'carrier_absent_minus_present_at_freeform':{'free_form__absent':1,'free_form__A.None':-1},
  'carrier_absent_minus_present_at_choice':{'choice__absent':1,'choice__A.None':-1},
  'interaction_instruction_gain_absent_minus_present':{'free_form__absent':1,'choice__absent':-1,'free_form__A.None':-1,'choice__A.None':1}}
 models=sorted({r['request_payload']['model'] for r in manifest});result={}
 for model in models:
  rows=[r for r in manifest if r['request_payload']['model']==model];n=len({r['source_sha256'] for r in rows});assert n==20
  counts={}
  for cond in sorted({r['condition'] for r in rows}):
   vals=[byid.get(r['trial_id']) for r in rows if r['condition']==cond]
   counts[cond]={'planned':len(vals),'known_correct':sum(x==1 for x in vals),'known_incorrect':sum(x==0 for x in vals),'unknown':sum(x is None for x in vals)}
  effects={}
  for name,coeff in functions.items():
   lo=hi=0
   for row in rows:
    c=coeff.get(row['condition'],0);v=byid.get(row['trial_id']);minimum,maximum=(v,v) if v is not None else (0,1)
    lo+=c*(minimum if c>=0 else maximum);hi+=c*(maximum if c>=0 else minimum)
   effects[name]={'lower':lo/n,'upper':hi/n,'units':'score points on0..1 scale; interaction can range-2..2'}
  result[model]={'source_cases':n,'counts':counts,'contrasts':effects}
 return {'status':'COMPLETE_OFFLINE_ANALYSIS','planned':160,'scored_records_received':len(scores),'models':result,'new_api_calls':0,'interpretation':'Fixed-panel sensitivity bounds, not populationconfidenceintervals; score semantics belong to supplied verified scoring receipts.'}
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('scores',type=pathlib.Path);args=ap.parse_args();scores=[json.loads(l) for l in args.scores.read_text().splitlines()];print(json.dumps(analyze(scores),indent=2))
