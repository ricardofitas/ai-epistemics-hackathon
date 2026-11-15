"""Prospective 64 natural-pair analysis of authenticated native prediction ledger.
No provider imports or calls. Missing outputs enumerated jointly under both reference keys.
"""
from pathlib import Path
import argparse,json,itertools,random,collections,hashlib
MODELS=('deepseek-v4-flash','gemma-4-31b-it','glm-5.2','qwen3.8-27b');ARMS=('native_gallery','question_binding_fixed')
def delta(v,golds):
 native=lambda p:int(p[0]=='B' and p[1]=='B')
 source=lambda p:int(all(x==y for x,y in zip(p,golds)))
 return (source(v[2:])-source(v[:2]))-(native(v[2:])-native(v[:2]))
def unit_bounds(observed,golds):
 states=[('A','B',None) if not known else (value,) for known,value in observed]
 vals=[delta(v,golds) for v in itertools.product(*states)]
 return min(vals),max(vals)
def bootstrap(values,reps=10000):
 if not values:return None
 rng=random.Random(2026111501);out=sorted(sum(rng.choices(values,k=len(values)))/len(values) for _ in range(reps))
 return [out[int(.025*reps)],out[min(reps-1,int(.975*reps))]]
def analyze(spec,ledger):
 rows={};checks=0
 for r in ledger:
  key=(int(r['source_row_index']),r['model'],r['prompt_arm']);assert key not in rows,'duplicate native ledger cell';rows[key]=r
 allowed={(m['index'],model,arm) for p in spec['selected'] for m in p['members'] for model in MODELS for arm in ARMS};assert set(rows)<=allowed,'unplanned ledger cells'
 allpairs=[];permodel=collections.defaultdict(list)
 for p in spec['selected']:
  members=p['members'];golds=tuple(m['gold'] for m in members);units=[]
  for model in MODELS:
   observed=[]
   for armindex,arm in enumerate(ARMS):
    for m in members:
     row=rows.get((m['index'],model,arm));known=bool(row and row['response_available'] is True and row['comparison_known'] is True)
     if row:
      assert row['source_row_sha256']==m['source_sha256'];assert row['request_sha256']==m['requests_by_model'][model][armindex];assert row['gold_letter']==m['gold'];assert row['native_prediction'] in ('A','B',None)
      assert row['native_original_score']==int(row['native_prediction']=='B');assert row['native_source_score']==int(row['native_prediction']==m['gold']);checks+=1
     observed.append((known,row['native_prediction'] if known else None))
   lo,hi=unit_bounds(observed,golds);complete=all(x[0] for x in observed)
   unit={'model':model,'known_outputs':sum(x[0] for x in observed),'complete':complete,'delta_bounds':[lo,hi],'delta':lo if complete else None}
   assert not complete or lo==hi
   units.append(unit);permodel[model].append(unit)
  complete=all(u['complete'] for u in units)
  allpairs.append({'pair_id':p['selection_sha256'],'all_four_models_complete':complete,'delta_bounds':[sum(u['delta_bounds'][i] for u in units)/4 for i in [0,1]],'delta':sum(u['delta'] for u in units)/4 if complete else None,'models':units})
 n=len(allpairs);assert n==64
 mean_bounds=[sum(p['delta_bounds'][i] for p in allpairs)/n for i in [0,1]];complete=[p['delta'] for p in allpairs if p['all_four_models_complete']]
 return {'planned_source_pairs':n,'planned_distinct_source_questions':128,'planned_output_cells':1024,'provided_native_ledger_cells':len(rows),'identity_and_same_output_score_checks':checks,'primary_planned_pair_mean_identification_bounds':mean_bounds,'source_pairs_with_all_16_outputs_known':len(complete),'complete_all_models_pair_mean':sum(complete)/len(complete) if complete else None,'complete_all_models_pair_bootstrap95':bootstrap(complete),'per_model':{m:{'planned_pairs':64,'complete_pairs':sum(u['complete'] for u in us),'planned_mean_bounds':[sum(u['delta_bounds'][i] for u in us)/64 for i in [0,1]],'complete_pair_bootstrap95':bootstrap([u['delta'] for u in us if u['complete']])} for m,us in permodel.items()},'pair_details':allpairs,'scope':'Sharp missingness bounds on64plannedgroups, equally weighted fourfixedfamilies. Complete-case bootstrap is conditional on availability, not a replacement for planned-panel bounds or a population guarantee. Negative/zero contrasts retained. Not a new metric or generic theorem.'}
def self_test():
 spec={'selected':[{'selection_sha256':str(i),'members':[{'index':2*i,'gold':'A','source_sha256':str(2*i),'requests_by_model':{m:['n'+str(2*i),'f'+str(2*i)] for m in MODELS}},{'index':2*i+1,'gold':'B','source_sha256':str(2*i+1),'requests_by_model':{m:['n'+str(2*i+1),'f'+str(2*i+1)] for m in MODELS}}]} for i in range(64)]}
 a=analyze(spec,[]);assert a['primary_planned_pair_mean_identification_bounds']==[-2,2]
 for vals in itertools.product(('A','B',None),repeat=4):
  lo,hi=unit_bounds([(True,v) for v in vals],('A','B'));assert lo==hi==delta(vals,('A','B'))
  for mask in itertools.product((False,True),repeat=4):
   lo,hi=unit_bounds(list(zip(mask,vals)),('A','B'));assert lo<=delta(vals,('A','B'))<=hi
 assert unit_bounds([(True,x) for x in ('B','B','A','B')],('A','B'))==(2,2)
 assert unit_bounds([(True,x) for x in ('A','B','B','B')],('A','B'))==(-2,-2)
 return {'status':'PASS','enumerated_complete_units':81,'missingness_masks_per_unit':16,'complete_and_partial_controls':1296,'all_missing_planned64_bounds':[-2,2],'positive_and_negative_nonforced_witnesses':True,'new_model_calls':0}
def main():
 p=argparse.ArgumentParser();p.add_argument('--spec',type=Path);p.add_argument('--native-ledger',type=Path);p.add_argument('--out',type=Path,required=True);p.add_argument('--self-test',action='store_true');args=p.parse_args()
 if args.self_test:result=self_test()
 else:
  assert args.spec and args.native_ledger;spec=json.load(open(args.spec));rows=[json.loads(x) for x in args.native_ledger.read_text().splitlines() if x.strip()];result=analyze(spec,rows);result['input_sha256']={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [args.spec,args.native_ledger]}
 args.out.write_text(json.dumps(result,indent=2)+'\n');print({k:v for k,v in result.items() if k not in ['pair_details','per_model']})
if __name__=='__main__':main()
