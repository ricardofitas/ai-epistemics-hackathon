"""Independent read-only arithmetic/identity audit of the already captured natural baselines.
No native methods, model, CLI, source acquisition or inference is executed.
Never prints GPQA source question/answer text.
"""
from pathlib import Path
from collections import Counter
import json,hashlib,math,sys,zipfile
R=Path(__file__).resolve().parent
ART=R/'original';summary=json.loads((ART/'summary.json').read_bytes())
sha=lambda b:hashlib.sha256(b).hexdigest()
def canonical(v):return json.dumps(v,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()
def rows(p):return [json.loads(b) for b in p.read_bytes().splitlines() if b.strip()]
fail=[];out={};checks=0
def check(ok,message):
 global checks
 checks+=1
 if not ok:fail.append(message)
gold_keys={'cupcase':'correct_diagnosis','sciq':'correct_answer','gpqa':'Correct Answer'}
check(sha((R/'original.zip').read_bytes())=='ed328b8026f49436f0ab13e821c7ad87e2d3187737bcdb705f4b2625a63ede54','archive_digest')
for name,gold in gold_keys.items():
 d=summary['datasets'][name];folder=ART/'records'/name;allrows={label:rows(folder/f'constant-{label}.jsonl') for label in 'ABCD'}
 first=allrows['A'];n=len(first);check(n==d['source_rows'],name+':source_count')
 derived={'merged_choices','choices_text','generated_ans','eval_valid','eval_score','eval_pred','eval_error','eval_pred_choice','eval_ref_choice','eval_parse_strategy'}
 sourcekeys=set(first[0])-derived
 original_rows=[{k:x[k] for k in sorted(sourcekeys)} for x in first]
 source_digest=sha(canonical(original_rows))
 check(all(str(x[gold])==x['merged_choices'][0] for x in first),name+':gold_first_all')
 gold_positions=Counter(x['merged_choices'].index(str(x[gold])) for x in first)
 check({str(k):v for k,v in gold_positions.items()}==d['gold_position_counts'],name+':position_summary')
 labelresults={}
 for label,rr in allrows.items():
  check(len(rr)==n,name+':'+label+':row_count')
  check(sha(canonical([{k:x[k] for k in sorted(sourcekeys)} for x in rr]))==source_digest,name+':'+label+':same_source_columns')
  check(all(x['generated_ans']==f'<answer>{label}</answer>' for x in rr),name+':'+label+':literal_constant')
  valid=sum(x['eval_valid'] is True for x in rr);correct=sum(x['eval_valid'] is True and x['eval_score']==1 for x in rr)
  stat=json.loads((folder/f'stats-{label}.json').read_bytes())[0];b=d['baseline_results'][label]
  check(valid==b['native_valid']==stat['valid_samples'],name+':'+label+':valid_denominator')
  check(n-valid==b['invalid_references']==stat['invalid_references'],name+':'+label+':invalid_denominator')
  check(math.isclose(correct/valid,b['native_diagnostic_score']) and math.isclose(correct/valid,b['report_score']),name+':'+label+':native_report_arithmetic')
  check(stat['accuracy']==b['native_diagnostic_score'],name+':'+label+':pre-mark_native_stats')
  check(b['report_source']=='dataflow_eval:accuracy',name+':'+label+':report_selector_source')
  labelresults[label]={'correct':correct,'valid':valid,'invalid':n-valid,'report_score':b['report_score'],'stats_file_stage':'before_mark_diagnostic','ordinary_metric_score':b['ordinary_metric']['choice_accuracy']['score']}
 prompts=rows(folder/'prompt_index.jsonl')
 check(len(prompts)==n,name+':prompt_count')
 check(sum(x['own_question_present'] for x in prompts)==d['native_question_present'],name+':prompt_question_summary')
 check(sum(x['first_choice_present'] for x in prompts)==d['native_choices_present'],name+':prompt_first_option_summary')
 # Source-row hashes are opaque acquisition receipts, not independently recomputed from Parquet here.
 hashes=json.loads((folder/'source_row_hashes.json').read_bytes());check(len(hashes)==n and all(len(h)==64 for h in hashes),name+':source_receipt_count')
 out[name]={'rows':n,'source_gold_first':n,'captured_source_columns_sha256':source_digest,'label_results':labelresults,'source_ref_parse_positions':dict(Counter(str(x['eval_ref_choice']) for x in first)),'question_present':d['native_question_present'],'first_option_present':d['native_choices_present'],'source_hash_receipts':len(hashes)}
result={'status':'PASS'if not fail else'FAIL','checks':checks,'failures':fail,'datasets':out,'native_source_revision':summary['one_eval_revision'],'artifact_sha256':sha((R/'original.zip').read_bytes()),'scope':'Independent captured-record arithmetic/identity audit only. Original native/CLI methods not rerun; no historical affected conclusion established.','limitations':['Official raw Parquet/CSV acquisition hashes retained in originalsummary, not independently reacquired here.','Prompt text bytes not retained in originalartifact, only hashes/presence flags. This checks capture consistency, not independent re-rendering.','Ordinary metric score/report-selector score are different recorded stages; CLI closeout belongs to another executor.','All-A is a deterministic input-independent baseline, not measured LLM behavior.','Original GPQA question/answer content remains private and is not emitted in this report.'],'new_model_calls':0,'new_native_runs':0}
(R/'CAPTURE_VERIFICATION.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'status':result['status'],'checks':checks,'failures':fail,'rows':sum(d['rows'] for d in out.values()),'A_counts':{n:{k:v for k,v in d['label_results']['A'].items()if k in ['correct','valid','invalid','report_score']}for n,d in out.items()}}))
sys.exit(bool(fail))
