"""No network or provider requests; synthetic diagnostics on fixed source units."""
import sys,json,gzip,copy,hashlib,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parent
BASE=Path(sys.argv[1]).resolve()
def read(p):return [json.loads(x) for x in gzip.decompress(p.read_bytes()).splitlines()]
checker=BASE/'work/oneeval_contract_checker_20261114/check_contract.py'
assert hashlib.sha256(checker.read_bytes()).hexdigest()==json.loads((ROOT/'PROTOCOL.json').read_text())['frozen_v1_sha256']
shutil.copyfile(checker,ROOT/'check_contract.py')
sys.path.insert(0,str(ROOT))
from check_contract import audit_contract,guarded_inference,InvalidContract
from source_bound import audit_with_source,guarded_source_inference
conditions=list(json.loads((ROOT/'PROTOCOL.json').read_text())['conditions'])
records=[];summary=[];inputs=[]
for benchmark in ['mmlu','mmlu-pro']:
 source=read(BASE/'work/holdout/capture'/benchmark/'SELECTED.jsonl.gz')[:100]
 for selected in source:
  raw=selected['record'];q=raw['question'];opts=list(raw['choices'] if benchmark=='mmlu' else raw['options']);gold_index=int(raw['answer'] if benchmark=='mmlu' else raw['answer_index']);gold=opts[gold_index]
  assert len(opts)>=3 and gold and q
  wrong=next((i for i,x in enumerate(opts) if x!=gold),None)
  inputs.append(dict(benchmark=benchmark,**selected))
  for condition in conditions:
   row_id=benchmark+':'+str(selected['source_index'])+':'+condition
   if wrong is None and condition in ['distractor_replace','distractor_drop','duplicate_gold','wrong_reference']:
    records.append(dict(row_id=row_id,disposition='non_applicable',reason='no distinct distractor'));continue
   shown=list(opts);position=gold_index;correct=gold
   if condition=='trim_only':
    shown=[x.strip() for x in opts];correct=shown[position]
   elif condition=='coherent_permutation':
    shown=opts[1:]+opts[:1];position=(gold_index-1)%len(opts)
   elif condition=='distractor_replace':shown[wrong]='MUTATION_DISTRACTOR_'+row_id
   elif condition=='distractor_drop':
    shown.pop(wrong);position=gold_index-int(wrong<gold_index)
   elif condition=='duplicate_gold':shown[wrong]=gold
   elif condition=='gold_removed':shown[gold_index]='MUTATION_REMOVED_GOLD_'+row_id
   def render(question):
    if condition=='question_truncation':question=question[:max(1,len(question)//2)]
    if condition=='question_omission':question=''
    return question+'\n'+'\n'.join(chr(65+i)+'. '+x for i,x in enumerate(shown))+'\nSelect a letter.'
   prompt=render(q);label=chr(65+position)
   rec=dict(schema_version=1,row_id=row_id,kind='choice',prompt=prompt,choices=shown,correct_text=correct,expected_reference=label,reference=label,question_probe_changed=render('SOURCE_QUESTION_NONCE_'+row_id)!=prompt,context_required=False,context_probe_changed=None,source_question=q,source_choices=opts,source_correct_index=gold_index)
   if condition=='wrong_reference':rec['reference']=chr(65+wrong)
   if condition=='missing_source':
    for k in ['source_question','source_choices','source_correct_index']:rec.pop(k)
   v1=audit_contract([rec]);v2=audit_with_source([rec]);calls={}
   for version,guard in [('v1',guarded_inference),('v2',guarded_source_inference)]:
    seen=[]
    try:guard([rec],lambda prompts:seen.append(prompts))
    except InvalidContract:pass
    calls[version]=len(seen)
   records.append(dict(benchmark=benchmark,source_index=selected['source_index'],condition=condition,record=rec,v1=v1,v2=v2,backend_calls=calls,disposition='completed'))
for condition in conditions:
 subset=[r for r in records if r.get('condition')==condition and r['disposition']=='completed']
 summary.append(dict(condition=condition,rows=len(subset),v1={s:sum(r['v1']['status']==s for r in subset) for s in ['PASS','FAIL','INCOMPLETE']},v2={s:sum(r['v2']['status']==s for r in subset) for s in ['PASS','FAIL','INCOMPLETE']},backend_calls={v:sum(r['backend_calls'][v] for r in subset) for v in ['v1','v2']}))
(ROOT/'INPUTS.jsonl.gz').write_bytes(gzip.compress(b''.join(json.dumps(x,ensure_ascii=False).encode()+b'\n' for x in inputs),mtime=0))
(ROOT/'RESULTS.jsonl.gz').write_bytes(gzip.compress(b''.join(json.dumps(x,ensure_ascii=False).encode()+b'\n' for x in records),mtime=0))
result=dict(status='completed',source_units=len(inputs),condition_records=len(records),non_applicable=sum(r['disposition']!='completed' for r in records),provider_model_calls=0,controlled_backend_calls_are_not_model_requests=True,conditions=summary)
(ROOT/'SUMMARY.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
