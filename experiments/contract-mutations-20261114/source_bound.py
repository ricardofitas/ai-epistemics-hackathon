"""Experimental source-bound wrapper; frozen v1 is imported unchanged."""
from collections import Counter
from check_contract import audit_contract,InvalidContract
def audit_with_source(records):
 rows=list(records); native=audit_contract(rows);fail=Counter(native['failures']);incomplete=Counter(native['incomplete_checks'])
 for r in rows:
  q=r.get('source_question');opts=r.get('source_choices');pos=r.get('source_correct_index')
  if not isinstance(q,str) or not q.strip() or not isinstance(opts,list) or not opts or type(pos) is not int or not 0<=pos<len(opts) or any(not isinstance(x,str) for x in opts):
   incomplete['source_evidence_missing']+=1;continue
  prompt=r.get('prompt','')
  if not isinstance(prompt,str) or q.strip() not in prompt:
   fail['source_question_incomplete']+=1
  actual=r.get('choices')
  if not isinstance(actual,list) or any(not isinstance(x,str) for x in actual) or Counter(x.strip() for x in actual)!=Counter(x.strip() for x in opts):
   fail['source_choice_multiset_changed']+=1
  if not isinstance(r.get('correct_text'),str) or r['correct_text'].strip()!=opts[pos].strip():
   fail['source_gold_changed']+=1
 return dict(status='FAIL' if fail else 'INCOMPLETE' if incomplete else 'PASS',failures=dict(fail),incomplete_checks=dict(incomplete),records=len(rows),v1_status=native['status'])
def guarded_source_inference(records,generate):
 rows=list(records);report=audit_with_source(rows)
 if report['status']!='PASS':raise InvalidContract(report)
 return generate([r['prompt'] for r in rows])
