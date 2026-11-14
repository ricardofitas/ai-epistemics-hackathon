"""Independent byte/source/selection/request reconciliation and explicit adapter review."""
import json,gzip,hashlib
from pathlib import Path
from collections import Counter
P=Path(__file__).resolve().parent
canonical=lambda v:json.dumps(v,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()
load=lambda n:[json.loads(x) for x in gzip.decompress((P/n).read_bytes()).splitlines()]
selected=load('SELECTED.jsonl.gz');captures=load('CAPTURES.jsonl.gz');assert len(selected)==200 and len(captures)==600
lookup={(s['split'],s['source_index']):s for s in selected};assert len(lookup)==200
for split in ['free_form','multiple_choice']:
 rows=[json.loads(x) for x in (P/(split+'.jsonl')).read_bytes().splitlines()];order=sorted(range(len(rows)),key=lambda i:(hashlib.sha256(canonical(rows[i])).hexdigest(),i))[:100]
 assert [s['source_index'] for s in selected if s['split']==split]==order
 for i in order:assert lookup[(split,i)]['record']==rows[i]
seen=set();counts=Counter();trim_cases=set();dialect_cases=set()
for c in captures:
 key=(c['split'],c['source_index']);combo=(*key,c['condition']);assert combo not in seen;seen.add(combo);s=lookup[key];r=s['record'];assert hashlib.sha256(canonical(r)).hexdigest()==c['source_sha256'];assert hashlib.sha256(c['prompt'].encode()).hexdigest()==c['prompt_sha256']
 assert all(k in r for k in ['prompt','options','target','context']) and c['field_presence_check']
 if c['condition']=='native':assert not c['question_bound']
 else:assert c['question_bound'] and r['prompt'] in c['prompt']
 if c['split']=='free_form':
  assert r['problem_type']=='free-form' and c['displayed_choices']==['None']
  assert all(isinstance(x,str) for x in r['target'])
  if c['condition']=='bind_and_type':assert c['configured_eval_type']=='key2_q_ma' and c['source_type_preserved'] and not c['MC_instruction']
  else:assert c['configured_eval_type']=='key3_q_choices_a' and not c['source_type_preserved'] and c['MC_instruction'] and 'A. None' in c['prompt']
 else:
  assert r['problem_type']=='multiple-choice' and len(r['target'])==1 and all(str(x).isdigit() and 0<=int(x)<len(r['options']) for x in r['target'])
  assert c['configured_eval_type']=='key3_q_choices_a' and c['MC_instruction']
  assert [x.strip() for x in r['options']]==c['displayed_choices']
  if not c['source_type_preserved']:dialect_cases.add(key)
  if not c['choices_preserved']:trim_cases.add(key)
 counts[c['split']+':'+c['condition']]+=1
assert len(seen)==600 and all(n==100 for n in counts.values());assert len(dialect_cases)==100 and len(trim_cases)==1
review=dict(status='POST_OUTCOME_ADAPTER_REVIEW',original_results_retained=True,scientific_native_runs_repeated=False,type_dialect=dict(initial_expected='single-choice',observed='multiple-choice',source_rows=100,condition_appearances=300,reviewed_rule='Treat single-choice and multiple-choice as choice-family labels only when options are a list with at least2strings and every target is a legal integer index; this sample has exactly1target perrow.',reviewed_genuine_task_type_failures_on_MC=0),option_whitespace=dict(source_rows=1,condition_appearances=3,initial_exact_order_matches_per100=99,reviewed_normalized_order_matches_per100=100,rule='str.strip on each entire option, with order/length/content otherwise identical; no rematching or sample change.'),freeform_result_unchanged=True,qualification='Post-outcome review does not replace initial prospective metrics or claim unseen adapter validation.')
(P/'POSTHOC_ADAPTER_REVIEW.json').write_text(json.dumps(review,indent=2)+'\n')
report=dict(status='PASS',source_rows=200,condition_records=600,full_selected_coverage=True,freeform_native_task_type_failures=100,freeform_native_artificial_None_options=100,freeform_bind_only_task_type_failures=100,freeform_typed_generation_repairs=100,MC_reviewed_type_controls=100,MC_initial_exact_option_matches=99,MC_reviewed_option_matches=100,retained_type_dialect_audit_false_alerts=100,retained_whitespace_audit_alerts=1,provider_calls=0,scope='Source/capture/hash/selection reconciliation by same executor; no independent human review, no model/native-install/scoring execution.')
(P/'VERIFICATION.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
