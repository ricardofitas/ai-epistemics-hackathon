from pathlib import Path
from collections import Counter,defaultdict
import json,hashlib,gzip
R=Path(__file__).parent
canon=lambda x:json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()
sha=lambda x:hashlib.sha256(x).hexdigest()
w=R/'14137518822_payload/wino_track';v=R/'14137354329_payload/verifier_track'
load=lambda p:[json.loads(l) for l in p.read_bytes().splitlines() if l.strip()]
wm=load(w/'manifest.jsonl');vm=load(v/'manifest.jsonl');cm=load(v/'context-supplement-manifest.jsonl')
for rows,expected in [(wm,10136),(vm,9600),(cm,1600)]:
 assert len(rows)==expected;assert len({r['trial_id'] for r in rows})==expected
 for r in rows:assert sha(canon(r['request_payload']))==r['request_sha256'];assert r['request_payload']['max_tokens']==8192
assert len({r['trial_id'] for r in wm+vm+cm})==21336
cases=json.load(open(w/'cases.json'));byid={c['case_id']:c for c in cases};assert len(cases)==len(byid)==2534
models=sorted({r['request_payload']['model'] for r in wm});arms=sorted({r['prompt_arm'] for r in wm});counts=Counter((r['request_payload']['model'],r['prompt_arm']) for r in wm);assert set(counts.values())=={1267}
for c in cases:assert sha(canon(c['source_row']))==c['source_row_sha256'];assert c['gold_letter']=='AB'[int(c['source_row']['answer'])-1]
results=[];group_ledger=[]
for model in models:
 for arm in arms:
  cohort=[r for r in wm if r['request_payload']['model']==model and r['prompt_arm']==arm]
  for scope in ['all','prior_panel_excluded']:
   rows=[r for r in cohort if scope=='all' or not r['prior_model_panel']];g=defaultdict(list)
   for r in rows:
    c=byid[r['case_id']];assert r['source_row_sha256']==c['source_row_sha256'];assert r['source_row_index']==c['source_row_index']
    # Exact whole payload rather than just text; includes model, temperature, caps and messages.
    g[r['request_sha256']].append(c)
   error=0;conflict_rows=0;conflict_groups=0
   for key,cs in g.items():
    labels=Counter(c['gold_letter'] for c in cs);e=len(cs)-max(labels.values());error+=e
    if e:conflict_rows+=len(cs);conflict_groups+=1
    group_ledger.append({'model':model,'arm':arm,'scope':scope,'request_sha256':key,'gold_counts':dict(labels),'case_ids':[c['case_id'] for c in cs],'minimum_deterministic_errors':e})
   results.append({'model':model,'arm':arm,'scope':scope,'source_rows':len(rows),'unique_exact_payloads':len(g),'conflicting_groups':conflict_groups,'rows_in_conflicting_groups':conflict_rows,'minimum_deterministic_errors':error,'deterministic_prompt_only_max_correct':len(rows)-error,'deterministic_prompt_only_accuracy_ceiling':(len(rows)-error)/len(rows)})
# Verify repaired source row/pair identity without treating repeated models as new questions.
for q in range(1267):
 cs=[c for c in cases if c['source_row_index']==q];assert len(cs)==2 and cs[0]['source_row']==cs[1]['source_row']
 for c in cs:
  if c['prompt_arm']=='question_binding_fixed':assert c['source_row']['sentence'] in c['prompt']
# Confirm supplemental pair links bind actual fixed request hashes and original IDs.
orig={r['trial_id']:r for r in vm};sup={r['trial_id']:r for r in cm};links=[json.loads(l) for l in gzip.decompress((v/'CONTEXT_PAIR_LINKS.jsonl.gz').read_bytes()).splitlines()]
for l in links:
 a=orig[l['original_trial_id']];b=(orig if l['same_payload_reused'] else sup)[l['repaired_trial_id']]
 assert a['request_sha256']==l['original_request_sha256'];assert b['request_sha256']==l['repaired_request_sha256'];assert a['metadata']['row_id']==b['metadata']['row_id']==l['row_id'];assert a['request_payload']['model']==b['request_payload']['model']==l['model']
assert len(links)==1600
out={'status':'PASS_DESIGN_ONLY_NO_OUTPUTS_READ','planned_unique_trial_ids':21336,'wino_cells':dict((str(k),c) for k,c in counts.items()),'verifier_config_counts':dict(Counter(r['metadata']['config_id'] for r in vm)),'context_pair_links':len(links),'context_actual_payload_reuse':sum(l['same_payload_reused'] for l in links),'bounds':results,'limits':'Exact finite-panel deterministic bound or equal-within-group conditional expected accuracy; not a hard bound on finite stochastic draws. No model response terminals read or counted.'}
(R/'DESIGN_AUDIT.json').write_text(json.dumps(out,indent=2)+'\n');(R/'COLLISION_GROUPS.jsonl').write_text(''.join(json.dumps(g)+'\n' for g in group_ledger));print(json.dumps(out,indent=2))
