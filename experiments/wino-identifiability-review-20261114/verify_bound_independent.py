"""Independent exact-payload sort/run-length calculation; imports no production audit code."""
import json,hashlib,itertools
from pathlib import Path
R=Path(__file__).parent;w=R/'14137518822_payload/wino_track';cases={x['case_id']:x for x in json.load(open(w/'cases.json'))};rows=[json.loads(x) for x in (w/'manifest.jsonl').read_bytes().splitlines()];results=[]
for model in sorted({r['request_payload']['model'] for r in rows}):
 for arm in sorted({r['prompt_arm'] for r in rows}):
  for heldout in [False,True]:
   selected=[r for r in rows if r['request_payload']['model']==model and r['prompt_arm']==arm and not(heldout and r['prior_model_panel'])]
   tuples=sorted((json.dumps(r['request_payload'],sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False),int(cases[r['case_id']]['source_row']['answer'])-1) for r in selected)
   right=0;ng=0;conf=0
   for payload,group in itertools.groupby(tuples,key=lambda t:t[0]):
    ys=[y for _,y in group];a=ys.count(0);b=ys.count(1);right+=max(a,b);ng+=1;conf+=int(bool(a and b))
   results.append({'model':model,'arm':arm,'scope':'prior_panel_excluded' if heldout else 'all','source_rows':len(selected),'unique_exact_payloads':ng,'conflicting_groups':conf,'deterministic_prompt_only_max_correct':right})
audit=json.load(open(R/'DESIGN_AUDIT.json'))
for row in results:
 expected=next(x for x in audit['bounds'] if all(row[k]==x[k] for k in ['model','arm','scope']))
 for k,v in row.items():assert expected[k]==v,(k,v,expected[k])
for aid,digest in [('14137518822','eb18b401f553fcf9a8542c73a6ecfcfcf2c7e8004883e66ce8867cf5e72d37b9'),('14137354329','e55450fc0d5a334794b2fe54604d9979670d164cd185b95cc583f21a7957d4a4')]:
 assert hashlib.sha256((R/(aid+'.zip')).read_bytes()).hexdigest()==digest
(R/'BOUND_VERIFICATION.json').write_text(json.dumps({'status':'PASS','independent_algorithm':'Sort exact whole payload bytes, groupby then binary gold majority; no production audit imported','cohorts_checked':len(results),'artifact_digests_checked':2,'new_model_calls':0,'live_outputs_read':0},indent=2)+'\n');print('PASS',len(results),'cohorts and2artifactdigests')
