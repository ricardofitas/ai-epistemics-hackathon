"""Conservative prereview-rubric aggregation; does not modify individual labels."""
from pathlib import Path
import json,collections
P=Path(__file__).resolve().parent
ZERO={'SYMBOLIC','ABSENT','INCOMPATIBLE'}
def final(a,b):return 1 if a==b=='SUPPORTED' else 0 if a in ZERO and b in ZERO else None
def nonfinal(a,b):return 1 if a==b=='SUPPORTED' else 0 if a==b=='NOT_OBSERVED' else None
def bounds(v):return [sum(x or 0 for x in v),sum(1 if x is None else x for x in v)]
def main():
 reviews=[{x['opaque_id']:x for x in json.load(open(P/f'REVIEW_{k}.json'))} for k in ['A','B']]
 mapping=json.load(open(P/'PRIVATE_MAPPING.json'));blind={x['opaque_id']:x for x in json.load(open(P/'BLINDED_CASES.json'))}
 assert all(set(r)==set(blind) for r in reviews)
 records=[]
 for m in mapping:
  r=dict(m);r.update(final_score=None,nonfinal_score=None,labels=None)
  if m['included']:
   a,b=[v[m['opaque_id']] for v in reviews]
   r['final_score']=final(a['final_label'],b['final_label']);r['nonfinal_score']=nonfinal(a['nonfinal_label'],b['nonfinal_label']);r['labels']=[{'final':v['final_label'],'nonfinal':v['nonfinal_label']} for v in [a,b]]
  records.append(r)
 groups=[]
 for model in sorted({r['model'] for r in records}):
  for cond in ['binding_only','official_typed']:
   xs=[r for r in records if (r['model'],r['condition'])==(model,cond)];included=[r for r in xs if r['included']]
   assert len(xs)==20
   groups.append(dict(model=model,condition=cond,total=20,completed=len(included),capture_unknowns=20-len(included),original_rule_correct=sum(r['score'] for r in included),final_supported_bounds=bounds([r['final_score'] for r in xs]),nonfinal_supported_bounds=bounds([r['nonfinal_score'] for r in xs]),final_label_disagreements=sum(r['labels'][0]['final']!=r['labels'][1]['final'] for r in included),nonfinal_label_disagreements=sum(r['labels'][0]['nonfinal']!=r['labels'][1]['nonfinal'] for r in included),rule_credit_final_zero=sum(r['score']==1 and r['final_score']==0 for r in included),rule_credit_final_unknown=sum(r['score']==1 and r['final_score'] is None for r in included),supported_nonfinal_with_final_zero=sum(r['nonfinal_score']==1 and r['final_score']==0 for r in included),consensus_symbolic_final=sum(all(l['final']=='SYMBOLIC' for l in r['labels']) for r in included),rater_labels={str(i):{'final':dict(collections.Counter(r['labels'][i]['final'] for r in included)),'nonfinal':dict(collections.Counter(r['labels'][i]['nonfinal'] for r in included))} for i in [0,1]}))
 effects=[]
 for model in sorted({r['model'] for r in records}):
  by={(r['source_index'],r['condition']):r for r in records if r['model']==model};sources=sorted({k[0] for k in by});assert len(sources)==20
  item={'model':model,'source_questions':20}
  for endpoint in ['final_score','nonfinal_score']:
   lo=hi=0
   for s in sources:
    b=by[(s,'binding_only')][endpoint];t=by[(s,'official_typed')][endpoint]
    lo+=(0 if t is None else t)-(1 if b is None else b)
    hi+=(1 if t is None else t)-(0 if b is None else b)
   item[endpoint+'_gain_bounds']=[lo/20,hi/20]
  effects.append(item)
 report=dict(status='complete_dual_review',reviewed=69,capture_unknowns=11,provider_calls=0,assistant_reviewers=2,groups=groups,effects=effects,interpretation='Reference-grounded model-assisted output audit, not human gold validation, default judge, population accuracy or capability estimate. Incomplete captures and reviewer ambiguity/disagreement remain unknown. Same20question panel reused across2models.',protocol_commit='eee9572f4a45bd9479ccbe6dd7d9cd0c516454c5')
 (P/'ADJUDICATED_RECORDS.json').write_text(json.dumps(records,indent=2)+'\n');(P/'SUMMARY.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
