"""Source-authenticated existing-capture SQuAD consequence and closure audit."""
from pathlib import Path
import hashlib,gzip,json,importlib.util
from collections import Counter,defaultdict
import design,scoring

ROOT=Path(__file__).resolve().parent
def sha(b):return hashlib.sha256(b).hexdigest()
def canonical(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def module(path,name):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def main():
 pins=json.loads((ROOT/'SOURCE_PINS.json').read_bytes())
 for name,expected in pins.items():
  b=(ROOT/name).read_bytes();assert hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==expected
 inputs=ROOT/'inputs';receipts=json.loads((ROOT/'ACQUISITION.json').read_bytes())
 for row in receipts:assert sha((inputs/(row['name']+'.zip')).read_bytes())==row['sha256']
 cases=json.loads((ROOT/'cases.json').read_bytes());case_by_id={c['id']:c for c in cases if c['dataset']=='squad'};assert len(case_by_id)==100
 original=json.loads((ROOT/'squad-dev-original.json').read_bytes());assert hashlib.sha1(b'blob '+str((ROOT/'squad-dev-original.json').stat().st_size).encode()+b'\0'+(ROOT/'squad-dev-original.json').read_bytes()).hexdigest()=='e9a3f913ad1468ebe105b891334ca7b0bc0e2510'
 subset=[]
 for article in original['data']:
  selected=[]
  for para in article['paragraphs']:
   qas=[]
   for qa in para['qas']:
    if qa['id'] not in case_by_id:continue
    case=case_by_id[qa['id']]
    assert case['question']==qa['question'] and case['context']==para['context']
    assert case['gold']==list(dict.fromkeys(a['text'] for a in qa['answers']))
    assert case['record_sha']==sha(canonical([para['context'],qa]))
    assert all(para['context'][a['answer_start']:a['answer_start']+len(a['text'])]==a['text'] for a in qa['answers'])
    qas.append(qa)
   if qas:selected.append(dict(context=para['context'],qas=qas))
  if selected:subset.append(dict(title=article['title'],paragraphs=selected))
 official=module(ROOT/'official_squad_evaluate.py','official_squad_evaluate')
 attempts={};paths={};count=Counter()
 for path in sorted(inputs.glob('contract-transfer-wave-*/s*/attempts.jsonl')):
  for line in path.read_bytes().splitlines():
   a=json.loads(line);key=(a['key'],a['attempt']);assert key not in attempts
   attempts[key]=a;paths[key]=path.parent;count['attempts']+=1
 final={}
 for key in sorted(attempts,key=lambda x:(x[0],x[1])):
  row=attempts[key]
  if row['key'] in final:assert final[row['key']]['http']==429
  final[row['key']]=row
 source_rows=design.trials(cases);ledger=[];records={};checked=0
 for row in source_rows:
  case=cases[row['case']]
  if case['dataset']!='squad':continue
  a=final[row['key']];pay=design.payload(case,row['model'],row['arm'],row['case'])
  assert row['request_sha']==sha(canonical(pay))==a['request_sha']
  terminal=None
  if a.get('terminal_sha'):
   path=paths[(a['key'],a['attempt'])]/'terminal'/f"{a['key']}-{a['attempt']}.json.gz"
   b=gzip.decompress(path.read_bytes());assert sha(b)==a['terminal_sha'];terminal=json.loads(b)
   assert terminal['output_text']==a['text'] and sha(a['text'].encode())==a['output_sha']
   assert terminal['id']==a['response_id'] and terminal['model']==a['returned_model']
   assert bool(a['eligible'])==(a['http']==200 and terminal['status']=='completed')
  final_answer,route=scoring.final_text(a.get('text',''))
  known=bool(a['eligible'])
  em=official.metric_max_over_ground_truths(official.exact_match_score,final_answer,case['gold']) if known else None
  f1=official.metric_max_over_ground_truths(official.f1_score,final_answer,case['gold']) if known else None
  if known:assert int(em)==scoring.grade(case,a['text'])[0]
  rec=dict(key=row['key'],case_index=row['case'],source_id=case['id'],source_record_sha=case['record_sha'],model=row['model'],arm=row['arm'],
    eligible=known,request_sha=row['request_sha'],terminal_sha=a.get('terminal_sha'),output_sha=a.get('output_sha'),
    final=final_answer,extraction_route=route,official_em=em,official_f1=f1,
    dummy=bool(scoring.grade(case,a['text'])[1]) if known else None)
  ledger.append(rec);records[(row['model'],case['id'],row['arm'])]=rec;checked+=1
 assert checked==1600
 summary={};pairs={};full={}
 for model in design.MODELS:
  arms={}
  for arm in design.ARMS:
   predictions={source_id:records[(model,source_id,arm)]['final'] if records[(model,source_id,arm)]['eligible'] else '' for source_id in case_by_id}
   result=official.compute_score(subset,predictions)
   nunknown=sum(not records[(model,source_id,arm)]['eligible'] for source_id in case_by_id)
   assert result['exact_match']==sum(records[(model,i,arm)]['official_em'] or 0 for i in case_by_id)
   arms[arm]=dict(n=100,known=100-nunknown,unknown=nunknown,official_em_lower=result['exact_match'],official_em_upper=result['exact_match']+nunknown,
    official_f1_lower=result['f1'],official_f1_upper=result['f1']+nunknown)
  summary[model]=arms
  outcomes=Counter()
  for ident in case_by_id:
   clear=records[(model,ident,'choice_clear')];none=records[(model,ident,'choice_none')]
   if not clear['eligible'] or not none['eligible']:outcomes['unknown_pair']+=1;continue
   if clear['official_em'] and not none['official_em']:
    outcomes['clear_correct_none_wrong']+=1
    outcomes['clear_correct_none_dummy']+=bool(none['dummy'])
   elif none['official_em'] and not clear['official_em']:outcomes['none_correct_clear_wrong']+=1
   elif clear['official_em']:outcomes['both_correct']+=1
   else:outcomes['both_wrong']+=1
  outcomes['drop_lower_pp']=arms['choice_clear']['official_em_lower']-arms['choice_none']['official_em_upper']
  outcomes['drop_upper_pp']=arms['choice_clear']['official_em_upper']-arms['choice_none']['official_em_lower']
  pairs[model]=dict(outcomes)
 witnesses=[]
 for ident,case in case_by_id.items():
  selected=[]
  for model in design.MODELS:
   rows={arm:records[(model,ident,arm)] for arm in ['choice_clear','choice_none','free_none']}
   if all(r['eligible'] for r in rows.values()) and rows['choice_clear']['official_em'] and rows['free_none']['official_em'] and not rows['choice_none']['official_em'] and rows['choice_none']['dummy']:
    selected.append(dict(model=model,rows=rows))
  if selected:witnesses.append(dict(source=case,models=selected))
 witnesses.sort(key=lambda x:(-len(x['models']),sha(x['source']['id'].encode())))
 for witness in witnesses:
  for block in witness['models']:
   model=block['model'];case=witness['source'];index=block['rows']['choice_clear']['case_index']
   clear=design.payload(case,model,'choice_clear',index);none=design.payload(case,model,'choice_none',index)
   assert none['input']==clear['input'].replace('Put your final answer','Options:\nA. None\n\nPut your final answer')
   assert {k:v for k,v in clear.items() if k!='input'}=={k:v for k,v in none.items() if k!='input'}
 result=dict(status='PASS_OFFICIAL_SCORER_CAUSAL_PANEL_RECHECK',source_questions=100,planned_captured_requests=1600,
  complete=sum(x['eligible'] for x in ledger),unknown=sum(not x['eligible'] for x in ledger),
  model_calls=0,judge_calls=0,summary=summary,pairs=pairs,
  strongest_witness_models=len(witnesses[0]['models']) if witnesses else 0,witness_source_count=len(witnesses),
  official_scorer=dict(repository='huggingface/evaluate',path='metrics/squad/compute_score.py',git_blob='e60acfd1044319e43a59ffe8db75e63b68785ba7'),
  closure=dict(source_authentication='PASS',actual_serialized_request_hash='PASS',captured_final_answer='PASS',official_squad_metric_execution='PASS',
    one_eval_native_squad_generation='NOT_EXECUTED',natural_supported_native_fault_attribution='UNESTABLISHED',
    external_published_conclusion_changed='UNESTABLISHED',
    scope='Actual prospective standalone Adaption captures, not ordinary One-Eval SQuAD generation. Carrier manipulation was deliberately introduced; official SQuAD scorer was run directly on prespecified extracted final answers. This independently verifies the measured causal final-answer consequence, not natural pipeline prevalence or a published ranking reversal.'))
 (ROOT/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n')
 (ROOT/'OFFICIAL_SCORE_LEDGER.jsonl').write_text(''.join(json.dumps(x,sort_keys=True)+'\n' for x in ledger))
 (ROOT/'WITNESS.json').write_text(json.dumps(witnesses[0] if witnesses else {},indent=2)+'\n')
 print(json.dumps(result,indent=2))

if __name__=='__main__':main()
