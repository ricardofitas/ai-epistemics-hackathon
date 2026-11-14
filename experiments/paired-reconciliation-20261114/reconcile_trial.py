"""Reconcile pinned raw outputs and factor the two evaluation interventions."""
import sys,json,gzip,re,hashlib,copy
from collections import Counter,defaultdict
from decimal import Decimal
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parent
BASE=Path(sys.argv[1]).resolve();TRIAL=BASE/'oneeval_paired_20261114'
sys.path.insert(0,str(BASE/'default_contract_audit_20261113'))
import audit_contracts as native
native.load_components()
from one_eval.metrics.parsers import parse_value
def read(p):return [json.loads(x) for x in gzip.decompress(p.read_bytes()).splitlines()]
cases={r['source_row']:r for r in read(TRIAL/'fresh_panel.jsonl.gz')}
requests=read(TRIAL/'planned_requests.jsonl.gz')
responses=[json.loads(x) for x in (TRIAL/'capture/responses.jsonl').read_text().splitlines()]
byid={r['trial_id']:r for r in responses};assert len(requests)==len(byid)==len(responses)==200
source=read(native.CAPTURE/'winogrande__validation.jsonl.gz')
entry=next(r for r in json.loads((native.ROOT/'GALLERY_SELECTED.json').read_text())['benches'] if r['bench_name']=='winogrande')
parser=entry['meta']['evaluation']['parser']
source_order=sorted(cases)
rawrows=[copy.deepcopy(source[i]) for i in source_order]
frame,mapping=native.load_preprocessor()._preprocess_dataframe(pd.DataFrame(rawrows),'winogrande',copy.deepcopy(entry['meta']['key_mapping']),eval_type='key3_q_choices_a')
preprocessed=dict(zip(source_order,frame.to_dict('records')))
rows=[];cost=defaultdict(lambda:dict(requests=0,complete=0,input_tokens=0,output_tokens=0,total_tokens=0,reported_cost=Decimal(0)))
for req in requests:
 tid=req['trial_id'];r=byid[tid];case=cases[req['source_row']];official=source[req['source_row']]
 assert hashlib.sha256(json.dumps(official,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()==case['source_sha256']
 gold=chr(64+int(official['answer']));assert gold==case['gold']
 assert req['request_payload']==r['request_payload'];assert req['request_payload']['input']==case[req['condition']]
 assert r['attempt_count']==1 and r['usage']==r['raw_response']['usage']
 text=r.get('output_text') or ''
 assert hashlib.sha256(text.encode()).hexdigest()==r['output_text_sha256']
 tags=re.findall(r'<answer>\s*([A-Za-z])\s*</answer>',text)
 strict=tags[0].upper() if r['completed_nonempty'] and len(tags)==1 and tags[0].upper() in ['A','B'] else None
 native_row=preprocessed[req['source_row']]
 prediction=parse_value(text,parser,record=native_row)
 reference=parse_value(native_row[mapping['input_label_key']],parser,record=native_row)
 assert reference.ok and reference.normalized=='B'
 guessed=prediction.normalized if prediction.ok else None
 row=dict(trial_id=tid,model=req['request_payload']['model'],condition=req['condition'],source_row=req['source_row'],stratum=case['stratum'],group=case['dependency_group'],gold=gold,native_reference=reference.normalized,heuristic_prediction=guessed,strict_prediction=strict,completed=bool(r['completed_nonempty']),heuristic_shipped=int(guessed=='B'),heuristic_source=int(guessed==gold),strict_shipped=None if strict is None else int(strict=='B'),strict_source=None if strict is None else int(strict==gold))
 rows.append(row)
 u=r['usage'];bucket=cost[(row['model'],row['condition'])]
 bucket['requests']+=1;bucket['complete']+=row['completed']
 for k in ['input_tokens','output_tokens','total_tokens']:bucket[k]+=u[k]
 bucket['reported_cost']+=Decimal(str(u['cost']))
assert len(cases)==50 and len({x['group'] for x in rows})==35
original=json.loads((TRIAL/'RESULTS.json').read_text());factorizations=[];gains=[]
for model in sorted({x['model'] for x in rows}):
 for stratum in ['all_frozen_panel','contradictory_pair','singleton_control']:
  subset=[x for x in rows if x['model']==model and (stratum=='all_frozen_panel' or x['stratum']==stratum)]
  cells={}
  for condition in ['native_prompt','corrected_prompt']:
   panel=[x for x in subset if x['condition']==condition];n=len(panel)
   a=sum(x['heuristic_shipped'] for x in panel)/n;b=sum(x['heuristic_source'] for x in panel)/n
   old=next(x for x in original['raw_output_reference_replays'] if x['model']==model and x['stratum']==stratum and x['condition']==condition and x['predictor']=='model')
   assert a==old['shipped']['score'] and b==old['source_reference']['score']
   cells[condition]=dict(rows=n,shipped_score=a,source_score=b,strict_source_correct=sum(x['strict_source']==1 for x in panel),strict_unknown=sum(x['strict_source'] is None for x in panel))
  ns=cells['native_prompt']['shipped_score'];nc=cells['native_prompt']['source_score'];fs=cells['corrected_prompt']['shipped_score'];fc=cells['corrected_prompt']['source_score']
  interaction=(fc-fs)-(nc-ns);joint=fc-ns
  assert abs((fs-ns)+(fc-fs)-joint)<1e-12 and abs((nc-ns)+(fc-nc)-joint)<1e-12
  factorizations.append(dict(model=model,stratum=stratum,cells=cells,prompt_effect_with_shipped_refs=fs-ns,prompt_effect_with_source_refs=fc-nc,reference_effect_on_native_outputs=nc-ns,reference_effect_on_corrected_outputs=fc-fs,interaction=interaction,joint_assigned_score_effect=joint))
  paired=defaultdict(dict)
  for r in subset:paired[r['source_row']][r['condition']]=r['strict_source']
  lo=hi=observed=0
  for pair in paired.values():
   a=pair['native_prompt'];b=pair['corrected_prompt']
   observed+=(b or 0)-(a or 0);lo+=(b or 0)-(1 if a is None else a);hi+=(1 if b is None else b)-(a or 0)
  n=len(paired)
  gains.append(dict(model=model,stratum=stratum,pairs=n,unknown_zero_gain=observed/n,unknown_sensitivity=[lo/n,hi/n]))
resource_rows=[dict(model=k[0],condition=k[1],**{a:str(v) if isinstance(v,Decimal) else v for a,v in value.items()}) for k,value in sorted(cost.items())]
resource=dict(requests=200,complete=sum(x['completed'] for x in rows),attempts=200,incomplete=200-sum(x['completed'] for x in rows),input_tokens=sum(v['input_tokens'] for v in cost.values()),output_tokens=sum(v['output_tokens'] for v in cost.values()),total_tokens=sum(v['total_tokens'] for v in cost.values()),provider_reported_cost_units=str(sum((v['reported_cost'] for v in cost.values()),Decimal(0))),cost_currency=None,scope='This bounded200-request trial only; billed currency, project-wide cumulative spend and remaining credits unverified.',by_condition=resource_rows)
(ROOT/'RESOURCE_RECONCILIATION.json').write_text(json.dumps(resource,indent=2)+'\n')
(ROOT/'FACTORIZATION.json').write_text(json.dumps(dict(posthoc=True,factorizations=factorizations,strict_source_gains=gains),indent=2)+'\n')
(ROOT/'RECOMPUTED_ROWS.json').write_text(json.dumps(rows,indent=2)+'\n')
print(json.dumps(dict(resources=resource,all_panel_factorizations=[x for x in factorizations if x['stratum']=='all_frozen_panel'],all_panel_strict_gains=[x for x in gains if x['stratum']=='all_frozen_panel']),indent=2))
