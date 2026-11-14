"""Independent source/order/content checks for the remaining-split expansion."""
import json,gzip,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parent
BASE=Path(__import__('sys').argv[1]).resolve()
def rows(p):return [json.loads(x) for x in gzip.decompress(p.read_bytes()).splitlines()]
reports=json.loads((ROOT/'RESULTS.json').read_text())
checks=[]
for r in reports:
 assert r['status']=='completed'
 name=r['benchmark'];f=ROOT/'work/holdout/capture'/name;b=BASE/'artifact/capture'/name
 assert (f/'SOURCE_ROWS.jsonl.gz').read_bytes()==(b/'SOURCE_ROWS.jsonl.gz').read_bytes()
 full=rows(f/'SOURCE_ROWS.jsonl.gz');old={v['source_index'] for v in rows(b/'SELECTED.jsonl.gz')}
 new=rows(f/'SELECTED.jsonl.gz');native=rows(f/'CHECKER_NATIVE.jsonl.gz');reviewed=rows(f/'CHECKER_REVIEWED.jsonl.gz');repaired=rows(f/'CHECKER_REPAIRED.jsonl.gz')
 assert [x['source_index'] for x in new]==[i for i in range(len(full)) if i not in old]
 counts={'gold_absent_literal':0,'options_not_preserved_after_trim':0,'question_text_absent':0,'reviewed_reference_mismatch':0,'repaired_source_mismatch':0}
 for selected,raw,rev,fix in zip(new,native,reviewed,repaired):
  i=selected['source_index'];source=full[i];assert selected['record']==source
  if name in ('arc-challenge','openbookqa'):
   opts=source['choices']['text'];pos=list(map(str,source['choices']['label'])).index(str(source['answerKey']));q=source.get('question',source.get('question_stem'))
  else:
   opts=source['choices'] if name=='mmlu' else source['options'];pos=source['answer'] if name=='mmlu' else source['answer_index'];q=source['question']
  gold=opts[pos];label=chr(65+pos)
  counts['gold_absent_literal']+=gold not in (raw['choices'] or [])
  counts['options_not_preserved_after_trim']+=raw['choices']!=[v.strip() for v in opts]
  counts['question_text_absent']+=q not in (raw['prompt'] or '')
  if raw['choices']==[v.strip() for v in opts]:
   counts['reviewed_reference_mismatch']+=rev['reference']!=label or rev['expected_reference']!=label or rev['correct_text']!=opts[pos].strip()
  counts['repaired_source_mismatch']+=fix['choices']!=opts or fix['reference']!=label or fix['correct_text']!=gold or q not in fix['prompt']
 assert counts['gold_absent_literal']==r['native']['native_checker']['failures'].get('correct_choice_missing',0)
 assert counts['repaired_source_mismatch']==counts['reviewed_reference_mismatch']==0
 assert r['native']['repaired_checker']['status']=='PASS'
 assert r['native']['corrected_reference_oracle']['score']==1
 assert r['native']['corrected_reference_oracle']['scored_samples']==len(new)
 checks.append(dict(benchmark=name,new_rows=len(new),source_rows=len(full),disjoint_selection_verified=True,source_bytes_unchanged=True,independent_counts=counts,
  raw_status=r['native']['native_checker']['status'],reviewed_status=r['reviewed_checker']['status'],reviewed_failures=r['reviewed_checker']['failures'],
  raw_false_alert_rows_removed=sum(1 for a,b in zip(native,reviewed) if a!=b)))
result=dict(status='PASS',new_rows=sum(c['new_rows'] for c in checks),previous_rows_excluded=400,model_calls=0,checks=checks,
 limits='Verifies source binding and measured transformations on captured data; not model performance or external impact.')
(ROOT/'INDEPENDENT_CHECKS.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))

